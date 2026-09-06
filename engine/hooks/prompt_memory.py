#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prompt_memory.py — UserPromptSubmit hook: inject the memory relevant to what you
just typed.

Ranked recall (BM25) across every project Claude Code knows about, plus any extra
layers declared in config.json. Falls back to a keyword map, and then to silence.
Nothing here is ever fatal: a failure means this prompt gets no memory, never that
the session breaks.

Registered by install.sh as a UserPromptSubmit hook (5s timeout).

Stdlib only. No LLM calls, no API key, no server.
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory_config as cfgmod          # noqa: E402

RECALL_LOG = Path(__file__).resolve().parent / "recall.log"
LOG_MAX_BYTES = 1_000_000


# ---------------------------------------------------------------------------
# keyword fallback — used when there is no index, or the search finds nothing
# ---------------------------------------------------------------------------
def keyword_context(prompt: str, memory_dir: Path, cfg: dict):
    low = prompt.lower()
    per_file = int(cfg.get("max_chars_per_block", 1200))
    total_cap = int(cfg.get("max_total_chars", 3000))
    wanted = []
    for rule in cfg.get("keywords") or []:
        if any(str(k).lower() in low for k in rule.get("match") or ()):
            for f in rule.get("files") or ():
                if f not in wanted:
                    wanted.append(f)
    if not wanted:
        return None
    sections, total = [], 0
    for rel in wanted:
        if total >= total_cap:
            break
        path = memory_dir / rel
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2].strip()
        content = content[:per_file]
        if content:
            sections.append(content)
            total += len(content)
    return "\n\n---\n\n".join(sections) if sections else None


# ---------------------------------------------------------------------------
# ranked recall
# ---------------------------------------------------------------------------
def ranked_context(prompt: str, cwd: str, t0: float, cfg: dict):
    """Returns ((context, meta), reason). Context is None when nothing is injected.

    The `reason` matters as much as the result, because the two ways of getting
    no memory need OPPOSITE fixes and used to log the same string:
      "budget"  — the search worked but ran past budget_ms and was DISCARDED.
                  Fix: performance.
      "nohit"   — the search ran in time and found nothing relevant.
                  Fix: coverage, or the note's wording.
      "noindex" — no index and no cache to read.
                  Fix: run reindex_memory.py.
    Without that distinction there is no baseline, and you cannot tell whether a
    change improved recall or silently switched the engine off.
    """
    import memory_lib as ml

    budget = float(cfg.get("budget_ms", 1000))
    top_k = int(cfg.get("top_k", 5))
    project = ml.detect_project(cwd) if cwd else ""

    idx = ml.load_index()
    if idx:
        hits = ml.bm25_search_idx(prompt, idx, project, top_k=top_k)
        engine = "index"
    else:
        cache = ml.load_cache()
        if not cache:
            return (None, None), "noindex"
        hits = ml.bm25_search(prompt, cache, project, top_k=top_k)
        engine = "cache"

    # The guard is checked AFTER load+search, so by the time it fires the whole
    # cost is already paid. Discarding does not give any time back — it just
    # spends the time and returns nothing. That is why the budget is generous:
    # it exists for the pathological case (stalled disk, corrupt index), not to
    # shave milliseconds. Set it too low and you pay full price for no memory.
    if (time.perf_counter() - t0) * 1000 > budget:
        return (None, None), "budget"
    if not hits:
        return (None, None), "nohit"

    per_file = int(cfg.get("max_chars_per_block", 1200))
    total_cap = int(cfg.get("max_total_chars", 3000))
    sections, total, used = [], 0, []
    for score, n in hits:
        title = n.get("name") or Path(n["file"]).stem
        block = f"**[{n['project']}] {title}** — {n.get('description', '')}"
        snippet = n.get("snippet", "")
        if snippet:
            block += f"\n{snippet}"
        block = block[:per_file]
        if total + len(block) > total_cap:
            break
        sections.append(block)
        total += len(block)
        used.append((round(score, 1), n["project"], Path(n["file"]).name))
    if not sections:
        return (None, None), "nosections"
    return ("\n\n---\n\n".join(sections), {"project": project, "used": used,
                                           "engine": engine}), "ok"


def log_recall(line: str, cfg: dict):
    if not cfg.get("log_recall", True):
        return
    try:
        if RECALL_LOG.exists() and RECALL_LOG.stat().st_size > LOG_MAX_BYTES:
            RECALL_LOG.replace(RECALL_LOG.with_suffix(".log.1"))
        with RECALL_LOG.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def emit(context: str):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": f"## Relevant memory\n\n{context}",
    }}))


def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except Exception:
        sys.exit(0)

    cfg = cfgmod.load()
    prompt = data.get("prompt", "")
    if not prompt or len(prompt.strip()) < int(cfg.get("min_prompt_len", 12)):
        sys.exit(0)

    cwd = data.get("cwd", "") or os.getcwd()
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    t0 = time.perf_counter()
    try:
        (context, meta), reason = ranked_context(prompt, cwd, t0, cfg)
        ms = (time.perf_counter() - t0) * 1000
        if context:
            log_recall(f"{ts}\t{meta['engine']}\t{meta['project']}\t{ms:.0f}ms\t"
                       f"{prompt[:60]!r}\t{meta['used']}", cfg)
            emit(context)
            sys.exit(0)
        log_recall(f"{ts}\t{reason}->keywords\t{ms:.0f}ms\t{prompt[:60]!r}", cfg)
    except Exception as e:
        log_recall(f"{ts}\terror->keywords\t{type(e).__name__}: {e}\t{prompt[:60]!r}", cfg)

    context = keyword_context(prompt, cfgmod.memory_dir_for(cwd), cfg)
    if context:
        emit(context)
    sys.exit(0)


if __name__ == "__main__":
    main()
