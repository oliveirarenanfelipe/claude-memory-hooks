#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fixture_env.py — point the hooks at the synthetic corpus in tests/fixtures.

Why a fixture corpus at all: a test suite that reads your real notes proves
nothing to anyone else, cannot run in CI, and — worse — the version of this that
existed before MOVED the live cache aside while it ran, which broke recall for
whatever session happened to be open. These tests never touch your notes.

Called by: tests/golden_recall.py, tests/test_memory.py.
"""
import json
import os
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_DIR = TESTS_DIR.parent
FIXTURE_HOME = TESTS_DIR / "fixtures" / "claude_home"
HOOKS_DIR = REPO_DIR / "hooks"

# Fake cwds, matching the encoded folder names under fixtures/claude_home/projects.
API = r"C:\demo\code\api-server"
WEB = r"C:\demo\code\web-app"
NOTES = r"C:\demo\code\field-notes"


def setup(**overrides):
    """Write the fixture config, point CLAUDE_HOME at it, import the hooks.

    Returns (memory_config, memory_lib). Safe to call more than once.
    """
    cfg = {
        "language": "en",
        "project_roots": ["C:/demo/code"],
        "layers": [
            {
                "name": "handbook",
                "path": str(FIXTURE_HOME / "handbook"),
                "mode": "flat",
                "scope": "global",
            }
        ],
    }
    cfg.update(overrides)

    config_path = FIXTURE_HOME / "memory-hooks" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    os.environ["CLAUDE_HOME"] = str(FIXTURE_HOME)
    if str(HOOKS_DIR) not in sys.path:
        sys.path.insert(0, str(HOOKS_DIR))

    import memory_config as cfgmod
    # The module resolves its paths at import time, so a second call must refresh
    # them explicitly rather than rely on the environment variable alone.
    cfgmod.CLAUDE_DIR = FIXTURE_HOME
    cfgmod.CONFIG_PATH = config_path
    cfgmod.PROJECTS_DIR = FIXTURE_HOME / "projects"
    cfgmod.INDEX_DIR = cfgmod.PROJECTS_DIR / "_index"
    cfgmod.CACHE_PATH = cfgmod.INDEX_DIR / "memory_cache.json"
    cfgmod.INDEX_PATH = cfgmod.INDEX_DIR / "memory_index.pkl"
    cfgmod.load(refresh=True)

    import memory_lib as ml
    ml.PROJECTS_DIR = cfgmod.PROJECTS_DIR
    ml.CACHE_PATH = cfgmod.CACHE_PATH
    ml.INDEX_PATH = cfgmod.INDEX_PATH
    return cfgmod, ml


def fresh_index(ml):
    """Rebuild cache and index from the fixture corpus, from scratch."""
    for p in (ml.CACHE_PATH, ml.INDEX_PATH):
        try:
            p.unlink()
        except Exception:
            pass
    ml.build_cache(only_changed=False)
    return ml.build_index(force=True)
