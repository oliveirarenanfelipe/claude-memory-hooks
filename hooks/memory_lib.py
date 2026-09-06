#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
memory_lib.py — the retrieval core: scan notes, build an index, rank with BM25.

Markdown is the source of truth. Everything this file writes (`memory_cache.json`,
`memory_index.pkl`) is derived and can be deleted at any time — the next reindex
rebuilds it. This module NEVER writes to a `.md` file.

Called by: prompt_memory.py, reindex_memory.py, tests/test_memory.py,
tests/golden_recall.py.

Stdlib only. No external dependencies, no API keys, no server.
"""
import json
import math
import os
import pickle
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

import memory_config as cfgmod

PROJECTS_DIR = cfgmod.PROJECTS_DIR
CACHE_PATH = cfgmod.CACHE_PATH
INDEX_PATH = cfgmod.INDEX_PATH

# Bump when the structure of the index changes (a new layer, a new field).
# Without this, an old index survives a code change and the new layer never
# appears — silently. Measured failure mode: a whole layer stayed invisible for
# days because the staleness guard only compared file counts and timestamps, and
# moving files preserves timestamps.
INDEX_VERSION = 1

_FRONT_RE = {
    "name": re.compile(r"^name:\s*(.+)$", re.M),
    "description": re.compile(r"^description:\s*(.+)$", re.M),
    "scope": re.compile(r"^\s*scope:\s*(\w+)", re.M),
}


# ---------------------------------------------------------------------------
# identity — re-exported so callers have one import
# ---------------------------------------------------------------------------
def detect_project(cwd: str) -> str:
    return cfgmod.detect_project(cwd, cfgmod.load())


def project_dir_to_slug(dirname: str) -> str:
    return cfgmod.slug_from_dirname(dirname, cfgmod.load())


def tokenize(text: str):
    """Lowercase + unicode-aware split. Keeps acronyms and IDs; no stemming.

    Deliberately not stemmed: `40A`, a ticket id, a model number are the terms
    that make a search precise. The cost is that "screen" and "screens" are
    different terms — which is why a note can declare extra trigger words in its
    frontmatter (see `_trigger_variants`).
    """
    stop = cfgmod.stopwords()
    return [w for w in re.split(r"[^0-9a-zà-öø-ÿ]+", text.lower())
            if len(w) >= 2 and w not in stop]


def _trigger_variants(text: str) -> str:
    """Singular/plural of each word, so one letter cannot hide a note.

    `tokenize` does no stemming, so a note whose trigger says "screen" is
    unreachable when the user types "screens". A nonsense variant is harmless —
    it simply matches nothing.
    """
    out = []
    for w in re.findall(r"[a-zA-ZÀ-ÿ]{4,}", text):
        wl = w.lower()
        out.append(wl[:-1] if wl.endswith("s") else wl + "s")
    return " ".join(dict.fromkeys(out))


# ---------------------------------------------------------------------------
# reading notes
# ---------------------------------------------------------------------------
def iter_memory_dirs():
    """(slug, Path) for every project memory folder Claude Code has created."""
    cfg = cfgmod.load()
    if not PROJECTS_DIR.is_dir():
        return
    for d in sorted(PROJECTS_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        mem = d / "memory"
        if mem.is_dir():
            yield cfgmod.slug_from_dirname(d.name, cfg), mem


def parse_note(path: Path):
    """name / description / scope / snippet from a note. None if unreadable."""
    try:
        txt = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    name = desc = scope = ""
    body = txt
    if txt.startswith("---"):
        parts = txt.split("---", 2)
        if len(parts) >= 3:
            fm, body = parts[1], parts[2]
            for key, rx in _FRONT_RE.items():
                m = rx.search(fm)
                if m:
                    val = m.group(1).strip().strip('"').strip("'")
                    if key == "name":
                        name = val
                    elif key == "description":
                        desc = val
                    elif key == "scope":
                        scope = val.lower()
    body_norm = re.sub(r"\s+", " ", body).strip()
    # snippet = what gets INJECTED (kept short); index_text = what gets tokenised
    # (more surface to match on without inflating the injected context).
    return {"name": name, "description": desc, "scope": scope or "project",
            "snippet": body_norm[:300], "index_text": body_norm[:1500]}


def slice_by_heading(text: str):
    """[(heading, body)] per '## ' section. [] when the note has no sections."""
    sections, current, label = [], [], None
    for ln in text.split("\n"):
        if ln.startswith("## "):
            if current and label:
                sections.append((label, "\n".join(current)))
            label = ln[3:].strip()
            current = [ln]
        else:
            current.append(ln)
    if current and label:
        sections.append((label, "\n".join(current)))
    return sections


def _layer_files(layer: dict):
    """Files of one configured layer, honouring its whitelist and mode."""
    path = Path(str(layer.get("path", "")).strip())
    if not path.is_dir():
        return
    folders = layer.get("folders")
    if folders:
        # Whitelist: a shallow glob per named subfolder. Shallow ON PURPOSE —
        # no subfolder joins the index without an explicit decision. This is the
        # guard that keeps scratch files and credential dumps out.
        for sub in folders:
            d = path / sub
            if d.is_dir():
                for f in sorted(d.glob("*.md")):
                    yield f, sub
        return
    it = path.rglob("*.md") if layer.get("mode") == "recursive" else path.glob("*.md")
    for f in sorted(it):
        yield f, ""


def iter_layer_notes(layer: dict):
    """(name, description, body, file) for one layer, sliced when large."""
    cfg = cfgmod.load()
    chunk_min = int(cfg.get("chunk_min", 5000))
    label = layer.get("name") or "layer"
    for f, sub in _layer_files(layer):
        try:
            txt = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if not txt.strip():
            continue
        where = f"{label}/{sub}" if sub else label
        desc = f"note from the {where} layer ({f.name})"
        trigger = ""
        m = _FRONT_RE["description"].search(txt[:4000]) if txt.startswith("---") else None
        if m:
            trigger = m.group(1).strip().strip('"').strip("'")
            desc = f"{desc} — {trigger}"[:800]
        # A "card": a short entry holding only identity + triggers, no body.
        # Why it exists: BM25 normalises by length (b=0.75), so a large document
        # loses to a small one even on a term that is genuinely its own. The card
        # puts them on the same footing. Dedup by file keeps card and slices from
        # taking two of the five slots.
        if layer.get("card") and trigger:
            yield (f"{f.stem} — when to use"[:140], desc,
                   f"{f.stem}. {trigger}. {_trigger_variants(trigger)}", f)
            continue
        if len(txt) >= chunk_min:
            sections = slice_by_heading(txt)
            if len(sections) >= 2:
                for head, body in sections:
                    yield (f"{f.stem} — {head}"[:140], desc, body, f)
                continue
        yield (f.stem[:140], desc, txt, f)


# ---------------------------------------------------------------------------
# cache (v1) — simple list of notes with their tokens
# ---------------------------------------------------------------------------
def build_cache(only_changed: bool = True):
    """Build/refresh the flat cache. Atomic write; pure stdlib."""
    cfg = cfgmod.load()
    skip = set(cfg.get("skip_filenames") or ())
    t0 = time.perf_counter()
    prev = {}
    if only_changed:
        old = load_cache()
        if old:
            prev = {n["file"]: n for n in old.get("notes", [])}

    notes, seen, reindexed = [], set(), 0
    for slug, mem in iter_memory_dirs():
        for f in mem.glob("*.md"):
            if f.name in skip:
                continue
            fp = str(f)
            seen.add(fp)
            try:
                mtime = f.stat().st_mtime
            except Exception:
                continue
            cached = prev.get(fp)
            if cached and abs(cached.get("mtime", 0) - mtime) < 1e-6:
                notes.append(cached)
                continue
            parsed = parse_note(f)
            if parsed is None:
                continue
            blob = f"{parsed['name']} {parsed['description']} {parsed['index_text']}"
            notes.append({
                "file": fp, "project": slug, "name": parsed["name"],
                "description": parsed["description"], "scope": parsed["scope"],
                "snippet": parsed["snippet"], "mtime": mtime, "tokens": tokenize(blob),
            })
            reindexed += 1

    notes = [n for n in notes if n["file"] in seen]   # drop deleted notes
    cache = {"version": 1, "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "notes": notes}
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE_PATH.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, CACHE_PATH)                       # atomic
    return {"total": len(notes), "reindexed": reindexed,
            "ms": (time.perf_counter() - t0) * 1000}


def load_cache(silent: bool = True):
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# inverted index — the fast path
# ---------------------------------------------------------------------------
# Why it exists, measured on a 949-note corpus:
#   flat cache (token list per note, df recomputed on every search):
#       load 54 ms + search p90 72 ms = 127 ms  -> 18.7% of prompts blew the
#       budget and LOST their memory entirely.
#   inverted index + pickle:
#       load 16 ms + search p90 1 ms  =  17 ms  -> 87% cheaper, smaller file,
#       and an IDENTICAL ranking on every regression case.
#
# Two deliberate choices:
#   - postings as a FLAT list [idx, tf, idx, tf, ...]: a list deserialises far
#     faster than a dict of tuples. Measured: a dict of term frequencies took
#     100 ms to load — worse than the flat cache — despite being fewer bytes.
#   - pickle rather than JSON: 16 ms against 64 ms for the same content. Safe
#     here because the file is derived, local and rebuildable, and never comes
#     from outside. If it fails to load, `load_index` returns None and the caller
#     falls back; the next reindex rebuilds it.

def index_needs_rebuild():
    """True when a note has changed, appeared or vanished since the last build.

    The reindex runs on every turn, so rebuilding unconditionally would waste
    most of a second for nothing. Comparing count + newest timestamp is cheap
    and sufficient. It must watch EXACTLY what the index contains, no more:
    watching a folder that is written on every turn (session briefs, an inbox
    fed by an external process) makes the index rebuild forever.
    """
    cfg = cfgmod.load()
    skip = set(cfg.get("skip_filenames") or ())
    try:
        idx = load_index()
        if not idx:
            return True
        if idx.get("version") != INDEX_VERSION:
            return True
        newest, count = 0.0, 0
        ok = True

        def visit(f):
            nonlocal newest, ok
            try:
                m = f.stat().st_mtime
            except Exception:
                ok = False
                return
            if m > newest:
                newest = m

        for _slug, mem in iter_memory_dirs():
            for f in mem.glob("*.md"):
                if f.name in skip:
                    continue
                count += 1
                visit(f)
        for layer in cfg.get("layers") or []:
            for f, _sub in _layer_files(layer):
                visit(f)
        if not ok:
            return True
        return count != idx.get("n_base", -1) or newest > idx.get("max_mtime", 0) + 1e-6
    except Exception:
        return True


def build_index(force: bool = False):
    """Build the inverted index from project notes plus every configured layer."""
    cfg = cfgmod.load()
    skip = set(cfg.get("skip_filenames") or ())
    note_cap = int(cfg.get("note_cap", 5000))
    chunk_min = int(cfg.get("chunk_min", 5000))
    t0 = time.perf_counter()
    if not force and not index_needs_rebuild():
        return {"notes": 0, "terms": 0, "mb": 0.0, "skipped": True,
                "ms": (time.perf_counter() - t0) * 1000}

    postings = defaultdict(list)
    meta = []
    max_mtime = 0.0
    n_base = 0                       # FILES under */memory — not slices, or the
                                     # staleness guard could never match again.

    def add(entry, tokens):
        i = len(meta)
        meta.append(entry)
        for w, tf in Counter(tokens).items():
            postings[w].append(i)
            postings[w].append(tf)

    for slug, mem in iter_memory_dirs():
        for f in mem.glob("*.md"):
            if f.name in skip:
                continue
            parsed = parse_note(f)
            if parsed is None:
                continue
            try:
                mtime = f.stat().st_mtime
            except Exception:
                continue
            max_mtime = max(max_mtime, mtime)
            n_base += 1

            try:
                raw = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                raw = ""
            body = raw
            if raw.startswith("---"):
                parts = raw.split("---", 2)
                if len(parts) >= 3:
                    body = parts[2]
            body_norm = re.sub(r"\s+", " ", body).strip()

            # The WHOLE body becomes indexable units. With only the first slice
            # indexed, anything written in the middle of a long note is
            # unreachable — measured at 35.8% of the corpus body reachable.
            units = []
            if len(body_norm) > chunk_min:
                sections = slice_by_heading(body)
                if len(sections) >= 2:
                    units = [(f" — {head}", text) for head, text in sections]
            if not units:
                units = [("", body_norm[:note_cap])]

            for suffix, text in units:
                tn = re.sub(r"\s+", " ", text).strip()[:note_cap]
                if not tn:
                    continue
                base = parsed["name"] or f.stem
                name = f"{base}{suffix}"[:140]
                toks = tokenize(f"{name} {parsed['description']} {tn}")
                if not toks:
                    continue
                add({"file": str(f), "project": slug, "name": name,
                     "description": parsed["description"], "scope": parsed["scope"],
                     "snippet": tn[:300], "mtime": mtime, "dl": len(toks)}, toks)

    for layer in cfg.get("layers") or []:
        lname = layer.get("name") or "layer"
        lscope = layer.get("scope") or "project"
        lweight = layer.get("weight")
        for name, desc, body, f in iter_layer_notes(layer):
            body_norm = re.sub(r"\s+", " ", body).strip()
            if not body_norm:
                continue
            toks = tokenize(f"{name} {desc} {body_norm[:note_cap]}")
            if not toks:
                continue
            try:
                mtime = f.stat().st_mtime
            except Exception:
                mtime = 0.0
            max_mtime = max(max_mtime, mtime)
            entry = {"file": str(f), "project": lname, "name": name,
                     "description": desc, "scope": lscope, "layer": lname,
                     "snippet": body_norm[:300], "mtime": mtime, "dl": len(toks)}
            if lweight is not None:
                entry["weight"] = float(lweight)
            add(entry, toks)

    # Session briefs are deliberately NOT indexed. session_context.py already
    # injects the current project's brief in full at session start, so indexing
    # it is redundant for the common case — and a brief is short and dense, which
    # BM25 favours, so it takes the top slot away from the curated note that
    # actually holds the answer. Tested with discounts from 0.85 down to 0.30:
    # no single value fixes both sides. A multiplicative discount is the wrong
    # tool for this; a reserved slot would be the right one, if ever needed.

    n = len(meta) or 1
    idx = {
        "version": INDEX_VERSION,
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "N": len(meta),
        "avgdl": sum(m["dl"] for m in meta) / n,
        "max_mtime": max_mtime,
        "n_base": n_base,
        "postings": dict(postings),
        "meta": meta,
    }
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Temp name carries the PID: the reindex runs on every turn, and parallel
    # agents mean simultaneous turns. A fixed temp name lets two processes write
    # the same file and promotes interleaved bytes.
    tmp = INDEX_PATH.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_bytes(pickle.dumps(idx, protocol=4))
    os.replace(tmp, INDEX_PATH)
    return {"notes": len(meta), "terms": len(postings),
            "mb": INDEX_PATH.stat().st_size / 1048576,
            "ms": (time.perf_counter() - t0) * 1000}


def load_index():
    """The inverted index, or None so the caller can fall back."""
    try:
        return pickle.loads(INDEX_PATH.read_bytes())
    except Exception:
        return None


# ---------------------------------------------------------------------------
# ranking
# ---------------------------------------------------------------------------
def _weight(m, current_project: str) -> float:
    """Ranking multiplier for one note, by where it comes from.

    Exclusive, not cumulative: a note in the open project does NOT also collect
    the global bonus. Stacking them made the open project win by 1.265x and
    silently invalidated the balance that was actually measured.
    """
    w = cfgmod.load().get("weights") or {}
    if current_project and m.get("project") == current_project:
        return float(w.get("current_project", 1.15))
    if m.get("weight") is not None:          # explicit per-layer weight wins
        return float(m["weight"])
    if m.get("scope") == "global":
        return float(w.get("global_scope", 1.10))
    if m.get("layer"):
        return float(w.get("default_layer", 0.70))
    return float(w.get("other_project", 0.50))


def _top_k_distinct(out, top_k: int):
    """Cut the top-k counting FILES, not fragments.

    Large notes are sliced, so one file can occupy several of the five slots.
    Without this, penalising other projects makes repetition WORSE: removing
    competitors just lets more slices of the same document rise. Measured across
    40 prompts: 4.65 -> 4.45 distinct files without dedup, 5.00/5 with it.
    """
    seen, res = set(), []
    for s, m in out:
        key = m.get("file")
        if key in seen:
            continue
        seen.add(key)
        res.append((s, m))
        if len(res) >= top_k:
            break
    return res


def bm25_search_idx(query, idx, current_project="", top_k=5, k1=1.5, b=0.75):
    """BM25 over the inverted index: only notes containing a query term are touched."""
    postings = idx.get("postings") or {}
    meta = idx.get("meta") or []
    if not meta:
        return []
    N = idx.get("N") or len(meta)
    avgdl = idx.get("avgdl") or 1.0
    acc = defaultdict(float)
    for w in tokenize(query):
        pl = postings.get(w)
        if not pl:
            continue
        dfw = len(pl) // 2
        idf = math.log(1 + (N - dfw + 0.5) / (dfw + 0.5))
        for j in range(0, len(pl), 2):
            i, tf = pl[j], pl[j + 1]
            dl = meta[i]["dl"] or 1
            acc[i] += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avgdl))
    out = [(s * _weight(meta[i], current_project), meta[i]) for i, s in acc.items()]
    out.sort(key=lambda x: -x[0])
    return _top_k_distinct(out, top_k)


def bm25_search(query: str, cache: dict, current_project: str = "", top_k: int = 5,
                k1: float = 1.5, b: float = 0.75):
    """Same ranking over the flat cache. Fallback path when there is no index."""
    notes = cache.get("notes", [])
    if not notes:
        return []
    q = tokenize(query)
    if not q:
        return []
    N = len(notes)
    avgdl = sum(len(n["tokens"]) for n in notes) / N or 1.0
    df = Counter()
    for n in notes:
        for w in set(n["tokens"]):
            df[w] += 1

    def idf(w):
        return math.log(1 + (N - df.get(w, 0) + 0.5) / (df.get(w, 0) + 0.5))

    out = []
    for n in notes:
        tf = Counter(n["tokens"])
        dl = len(n["tokens"])
        s = sum(idf(w) * (tf[w] * (k1 + 1)) / (tf[w] + k1 * (1 - b + b * dl / avgdl))
                for w in q if w in tf)
        if s <= 0:
            continue
        out.append((s * _weight(n, current_project), n))
    out.sort(key=lambda x: -x[0])
    return _top_k_distinct(out, top_k)
