#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_memory.py — the guards, tested against the fixture corpus.

    python tests/test_memory.py

No pytest, no dependencies, and it never touches your real notes or your live
index. Each block says what it protects; a test whose purpose you cannot name is
a test nobody will maintain.

Exit code: 0 = all pass · 1 = at least one failure.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fixture_env as fx                # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

cfgmod, ml = fx.setup()
fx.fresh_index(ml)

HOOKS = fx.HOOKS_DIR
PASS = FAIL = 0


def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}   {extra}")


def run_hook(script, payload):
    env = dict(os.environ)
    env["CLAUDE_HOME"] = str(fx.FIXTURE_HOME)
    p = subprocess.run([sys.executable, str(HOOKS / script)],
                       input=json.dumps(payload).encode(),
                       capture_output=True, env=env, timeout=60)
    return p.stdout.decode("utf-8", "replace").strip(), p.returncode


def context_of(out):
    try:
        return json.loads(out)["hookSpecificOutput"]["additionalContext"]
    except Exception:
        return ""


# ---------------------------------------------------------------------------
print("== folder encoding matches what Claude Code actually writes ==")
# Measured against real folders on disk. If this drifts, every path the hooks
# build points at a folder that does not exist, and memory silently disappears.
for cwd, expected in [
    (r"C:\demo\code\api-server", "C--demo-code-api-server"),
    (r"C:\demo\code\web-app", "C--demo-code-web-app"),
    ("C:/demo/code/field-notes", "C--demo-code-field-notes"),
    (r"C:\Users\me\Projects\Client Guimarães", "C--Users-me-Projects-Client-Guimar-es"),
]:
    got = cfgmod.encode_cwd(cwd)
    check(f"encode {cwd[-28:]!r}", got == expected, f"got {got!r}")

# ---------------------------------------------------------------------------
print("\n== project identity: both ends agree ==")
# The bug this protects against: the search read the PATH while the indexer read
# the FOLDER NAME. They diverged on any nested project, and 145 notes were
# treated as foreign inside their own project — scored at the neighbour penalty
# while sitting at home.
for cwd in [r"C:\demo\code\api-server",
            r"C:\demo\code\web-app",
            r"C:\demo\code\team\service\billing",
            r"C:\demo\code\team\service\billing\v2"]:
    a = cfgmod.detect_project(cwd)
    b = cfgmod.slug_from_dirname(cfgmod.encode_cwd(cwd))
    check(f"cwd and folder agree for {Path(cwd).name}", a == b, f"{a!r} != {b!r}")
check("a nested project is not collapsed into its parent",
      cfgmod.detect_project(r"C:\demo\code\team\service\billing")
      != cfgmod.detect_project(r"C:\demo\code\team\service"),
      cfgmod.detect_project(r"C:\demo\code\team\service\billing"))

# ---------------------------------------------------------------------------
print("\n== tokenizer keeps the terms that make a search precise ==")
tokens = ml.tokenize("unit 888675 ckTkU RS256 40A the of and")
for t in ["888675", "cktku", "rs256", "40a"]:
    check(f"kept: {t}", t in tokens, f"tokens={tokens}")
for t in ["the", "of", "and"]:
    check(f"dropped stopword: {t}", t not in tokens, f"tokens={tokens}")

# ---------------------------------------------------------------------------
print("\n== a broken config degrades to defaults instead of killing the hook ==")
backup = cfgmod.CONFIG_PATH.read_text(encoding="utf-8")
try:
    cfgmod.CONFIG_PATH.write_text("{ this is not json", encoding="utf-8")
    cfg = cfgmod.load(refresh=True)
    check("broken config falls back to defaults",
          cfg.get("budget_ms") == cfgmod.DEFAULTS["budget_ms"], str(cfg)[:80])
    out, rc = run_hook("prompt_memory.py",
                       {"prompt": "how do refresh tokens get rotated", "cwd": fx.API})
    check("hook still exits cleanly with a broken config", rc == 0, f"rc={rc}")
finally:
    cfgmod.CONFIG_PATH.write_text(backup, encoding="utf-8")
    cfgmod.load(refresh=True)

# ---------------------------------------------------------------------------
print("\n== recall arrives, and respects its caps ==")
out, rc = run_hook("prompt_memory.py",
                   {"prompt": "how do refresh tokens get rotated", "cwd": fx.API})
ctx = context_of(out)
check("memory is injected for a matching prompt",
      "Auth tokens" in ctx or "auth_tokens" in ctx, ctx[:120])
cfg = cfgmod.load()
check(f"context within cap ({cfg['max_total_chars']} + header)",
      len(ctx) <= cfg["max_total_chars"] + 200, f"len={len(ctx)}")
check(f"at most {cfg['top_k']} blocks",
      ctx.count("\n\n---\n\n") <= cfg["top_k"] - 1, "too many separators")

out, rc = run_hook("prompt_memory.py", {"prompt": "hi", "cwd": fx.API})
check("a prompt below min_prompt_len injects nothing", out == "", out[:80])

# ---------------------------------------------------------------------------
print("\n== no index and no cache: fall back, never crash ==")
saved = {}
for p in (ml.CACHE_PATH, ml.INDEX_PATH):
    if p.exists():
        saved[p] = p.read_bytes()
        p.unlink()
try:
    out, rc = run_hook("prompt_memory.py",
                       {"prompt": "how do refresh tokens get rotated", "cwd": fx.API})
    check("hook exits 0 with no index and no cache", rc == 0, f"rc={rc}")
    check("and injects nothing rather than garbage", context_of(out) == "", out[:80])
finally:
    for p, data in saved.items():
        p.write_bytes(data)

# ---------------------------------------------------------------------------
print("\n== budget guard: a slow search is discarded, not injected ==")
import prompt_memory as pm               # noqa: E402
(ctx, meta), reason = pm.ranked_context("refresh tokens", fx.API,
                                        time.perf_counter() - 10, cfgmod.load())
check(f"expired budget yields no context (reason={reason!r})", ctx is None, repr(ctx)[:80])
check("and says WHY, so the fix is not a guess", reason == "budget", reason)

# ---------------------------------------------------------------------------
print("\n== the staleness guard actually detects change ==")
ml.build_index(force=True)
check("nothing changed -> rebuild is skipped",
      ml.build_index().get("skipped") is True)
scratch = (fx.FIXTURE_HOME / "projects" / "C--demo-code-api-server" / "memory"
           / "_scratch_test_note.md")
try:
    scratch.write_text("---\nname: scratch\ndescription: temporary\n---\n\nbody\n",
                       encoding="utf-8")
    check("a new note -> rebuild is required", ml.index_needs_rebuild() is True)
finally:
    try:
        scratch.unlink()
    except OSError:
        pass
    ml.build_index(force=True)

# ---------------------------------------------------------------------------
print("\n== a hand-written brief is never destroyed ==")
# The bug this protects against: the previous guard also required the brief to
# carry the id of the session in progress — a condition nothing could satisfy —
# so every hand-written brief was overwritten on every single session.
briefs = cfgmod.briefs_dir_for(fx.API)
briefs.mkdir(parents=True, exist_ok=True)
brief_path = briefs / f"{cfgmod.detect_project(fx.API)}.md"
old_brief = brief_path.read_text(encoding="utf-8") if brief_path.exists() else None

transcript = fx.TESTS_DIR / "fixtures" / "_transcript.jsonl"
lines = []
for role, text in [("user", "please add the cardinality budget check to CI"),
                   ("assistant", "Added the check and wired it into the pipeline. "
                                 "Next step: watch the first run."),
                   ("user", "great, and update the handbook too"),
                   ("assistant", "Handbook updated in `handbook.md`. "
                                 "Blocked: waiting on the CI token.")]:
    lines.append(json.dumps({"message": {"role": role, "content": text}}))
transcript.write_text("\n".join(lines), encoding="utf-8")

try:
    curated = ("---\ncurated: true\n---\n\n**Date:** 2020-01-01\n\n"
               "Hand-written summary that must survive.\n")
    brief_path.write_text(curated, encoding="utf-8")
    run_hook("auto_brief.py", {"transcript_path": str(transcript), "cwd": fx.API,
                               "session_id": "s1"})
    after = brief_path.read_text(encoding="utf-8")
    check("curated brief survives the Stop hook",
          "Hand-written summary that must survive." in after, after[:120])
    check("and a dated footer says work happened after it",
          "<!-- unsaved-session:" in after, after[-160:])

    run_hook("auto_brief.py", {"transcript_path": str(transcript), "cwd": fx.API,
                               "session_id": "s1"})
    twice = brief_path.read_text(encoding="utf-8")
    check("the footer is idempotent per day, not stacked per turn",
          twice.count("<!-- unsaved-session:") == 1,
          str(twice.count("<!-- unsaved-session:")))

    brief_path.unlink()
    run_hook("auto_brief.py", {"transcript_path": str(transcript), "cwd": fx.API,
                               "session_id": "s1"})
    check("with no curated brief, one is generated", brief_path.exists())
    generated = brief_path.read_text(encoding="utf-8") if brief_path.exists() else ""
    check("the generated brief carries a next step",
          "Next step:" in generated, generated[:200])
    check("and reports the blocker it found",
          "waiting on" in generated.lower(), generated[-220:])

    print("\n== session start injects the brief back ==")
    out, rc = run_hook("session_context.py", {"cwd": fx.API})
    ctx = context_of(out)
    check("the brief comes back at session start", "Last session" in ctx, ctx[:120])
    check("without its frontmatter", "originSessionId" not in ctx, ctx[:120])
finally:
    try:
        transcript.unlink()
    except OSError:
        pass
    if old_brief is not None:
        brief_path.write_text(old_brief, encoding="utf-8")
    elif brief_path.exists():
        brief_path.unlink()

print(f"\n=== RESULT: {PASS} PASS / {FAIL} FAIL ===")
sys.exit(1 if FAIL else 0)
