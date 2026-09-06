#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
memory_config.py — every tunable knob of claude-memory-hooks, in one place.

Design rule for this whole project: **nothing about YOUR machine may live in the
code.** Paths, project names, keywords, language and ranking weights all come
from `~/.claude/memory-hooks/config.json`. The file is optional — with no config
at all the system still works, because the defaults below are the ones that were
actually measured in production (see `docs/MEASUREMENTS.md`).

Called by: memory_lib.py, prompt_memory.py, session_context.py, auto_brief.py,
reindex_memory.py, tests/test_memory.py, tests/golden_recall.py.

Stdlib only. No external dependencies, no API keys, no server.
"""
import json
import os
import re
from pathlib import Path

HOME = Path.home()
CLAUDE_DIR = Path(os.environ.get("CLAUDE_HOME") or (HOME / ".claude"))
CONFIG_PATH = CLAUDE_DIR / "memory-hooks" / "config.json"
PROJECTS_DIR = CLAUDE_DIR / "projects"
INDEX_DIR = PROJECTS_DIR / "_index"
CACHE_PATH = INDEX_DIR / "memory_cache.json"
INDEX_PATH = INDEX_DIR / "memory_index.pkl"

# ---------------------------------------------------------------------------
# Defaults. Every number here was measured, not guessed — the comment says on
# what. Override any of them in config.json without touching this file.
# ---------------------------------------------------------------------------
DEFAULTS = {
    # "en", "pt", or a list like ["en", "pt"] for a bilingual corpus.
    "language": "en",
    "extra_stopwords": [],

    # Folders that contain your projects, e.g. ["C:/Users/me/Projects"].
    # Used only to shorten project slugs: with the root declared, the project at
    # <root>/api-server gets the slug "api-server" instead of the full encoded
    # path. Leave empty and slugs fall back to the whole encoded folder name.
    "project_roots": [],

    # Extra note sources beyond ~/.claude/projects/*/memory. Each entry:
    #   name    — slug this layer's notes are filed under
    #   path    — folder to read
    #   mode    — "flat" (top level only) or "recursive"
    #   folders — optional whitelist of subfolders (each read flat)
    #   scope   — "global" (relevant in every project) or "project"
    #   weight  — optional explicit ranking multiplier for this layer
    # A whitelist is safer than a recursive sweep: it is what keeps an unrelated
    # subfolder (downloads, scratch files, credential dumps) out of the index.
    "layers": [],

    # --- ranking ------------------------------------------------------------
    # Measured on a 2,498-prompt log: 62.3% of injected notes came from OTHER
    # projects, and only 24.4% of those were marked global. The top-5 is a FIXED
    # number of slots, so a neighbour's note does not merely add noise — it
    # EVICTS the right one. These weights are multipliers, never filters: a
    # neighbour's note still wins when it is genuinely far more relevant.
    "weights": {
        "current_project": 1.15,
        "global_scope": 1.10,
        "other_project": 0.50,
        "default_layer": 0.70,
    },

    # --- budget -------------------------------------------------------------
    # The recall is DISCARDED if load+search exceeds this. Measured lesson: with
    # a 200 ms budget, 18.7% of prompts (155 of 830) lost their memory entirely,
    # 100% of them to the clock and none for lack of a result. The guard is
    # checked after the work is already paid for, so a tight budget makes the
    # prompt slower AND memoryless. 1000 ms keeps the protection against the
    # pathological case and stays 5x under the hook's own timeout.
    "budget_ms": 1000,

    "top_k": 5,
    "max_chars_per_block": 1200,
    "max_total_chars": 3000,
    "min_prompt_len": 12,

    # Notes longer than `chunk_min` are SLICED by "## " heading instead of being
    # truncated. Measured: with a 1500-char cap only 35.8% of the corpus body was
    # reachable; at 5000, 75.1%. Raising the cap further backfires — BM25
    # normalises by length (b=0.75), so a long document is penalised and drops
    # out of the top-10 even for a term it contains 84 times. Slicing is the only
    # move that makes every part of a long note reachable.
    "note_cap": 5000,
    "chunk_min": 5000,

    # Files never indexed. An auto-generated index page is 100% derived from the
    # descriptions of notes that are already indexed: indexing it duplicates the
    # same text and makes the map compete with the note it points at.
    "skip_filenames": ["MEMORY.md", "index.md", "README.md"],

    # Optional: `git pull` a notes repo at session start, for people who sync
    # memory between machines. Off by default.
    "sync": {"enabled": False, "path": "", "timeout": 60},

    # Keyword fallback, used when the index is missing or returns nothing.
    # [{"match": ["billing", "stripe"], "files": ["project_billing.md"]}]
    "keywords": [],

    # Keep a recall log (hooks/recall.log) so you can tell WHY a prompt got no
    # memory. See prompt_memory.py — "slow" and "no match" need opposite fixes.
    "log_recall": True,
}

# Short, functional words only. Acronyms and IDs are deliberately NOT stripped —
# "DR", "CC", "40A", a ticket number are exactly the terms that make a search
# precise, and a generic stopword list eats them.
STOPWORDS = {
    "en": (
        "a an the to of is in on and or as at be by for from has have it its "
        "that this these those was were will with we you they he she i do does "
        "did not no yes if then than so but our your their can could would "
        "should may might just about into over under more most some any"
    ).split(),
    "pt": (
        "a o e de da do das dos em no na nos nas um uma uns umas para por com "
        "que se ao aos os as ela ele eu te me la lo sua seu suas seus isso esse "
        "essa este esta isto ser ter foi sao são tem mais ja já nao não sim pra "
        "pro pelo pela como quando onde qual quais tudo todo toda muito"
    ).split(),
    "es": (
        "el la los las un una unos unas de del y o en para por con que se es "
        "son fue ser tener mas más ya no si como cuando donde cual todo muy"
    ).split(),
}

_cached = None


def _deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load(refresh: bool = False) -> dict:
    """The effective config: defaults with config.json merged over them.

    Never raises. A broken config.json degrades to the defaults rather than
    killing the hook — a memory system that breaks the session it was supposed
    to help is worse than no memory system.
    """
    global _cached
    if _cached is not None and not refresh:
        return _cached
    user = {}
    try:
        if CONFIG_PATH.exists():
            user = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        user = {}
    _cached = _deep_merge(DEFAULTS, user)
    return _cached


def stopwords(cfg: dict = None) -> set:
    cfg = cfg or load()
    langs = cfg.get("language") or "en"
    if isinstance(langs, str):
        langs = [langs]
    words = set()
    for lang in langs:
        words.update(STOPWORDS.get(str(lang).lower(), ()))
    words.update(w.lower() for w in cfg.get("extra_stopwords") or ())
    return words


# ---------------------------------------------------------------------------
# Project identity — ONE recogniser, used by both ends.
# ---------------------------------------------------------------------------
# Why this matters more than it looks: the indexer learns a project's identity
# from the FOLDER NAME, and the search learns it from the cwd. If those are two
# different functions, they drift — and a note stops being recognised as
# belonging to the project it is sitting in. Measured when that happened here:
# 145 notes inside their own project were scored as foreign (0.50 penalty) and
# the right answer fell out of the top-5. The fix is not a bigger lookup table;
# it is both ends calling the same function on the same string.

_KEEP = re.compile(r"[A-Za-z0-9-]")


def encode_cwd(cwd: str) -> str:
    """Reproduce how Claude Code names a project's folder under ~/.claude/projects.

    Measured against 23 real folders: every character that is not ASCII
    alphanumeric or a dash becomes a dash, with no collapsing — which is why
    `C:\\Users\\me` becomes `C--Users-me` (colon and backslash each yield one)
    and `Guimarães` becomes `Guimar-es`.
    """
    if not cwd:
        return ""
    cwd = str(cwd).rstrip("\\/")
    return "".join(c if _KEEP.match(c) else "-" for c in cwd)


def _root_prefixes(cfg: dict):
    for root in cfg.get("project_roots") or []:
        enc = encode_cwd(root).rstrip("-")
        if enc:
            yield enc + "-"


def slug_from_dirname(dirname: str, cfg: dict = None) -> str:
    """Encoded folder name -> short, stable project slug."""
    cfg = cfg or load()
    if not dirname:
        return ""
    name = dirname
    for prefix in _root_prefixes(cfg):
        if name.lower().startswith(prefix.lower()):
            name = name[len(prefix):]
            break
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def detect_project(cwd: str, cfg: dict = None) -> str:
    """cwd -> project slug. The single entry point; see the note above."""
    return slug_from_dirname(encode_cwd(cwd), cfg)


def memory_dir_for(cwd: str) -> Path:
    """Where Claude Code keeps this project's memory folder."""
    return PROJECTS_DIR / encode_cwd(cwd) / "memory"


def briefs_dir_for(cwd: str) -> Path:
    return memory_dir_for(cwd) / "session_briefs"
