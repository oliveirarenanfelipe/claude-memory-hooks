#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reindex_memory.py — keep the search index current.

    python reindex_memory.py             # incremental (default): only what changed
    python reindex_memory.py --rebuild   # full rebuild, ignoring the previous index
    python reindex_memory.py --quiet     # no output (how the hooks call it)

Registered by install.sh on SessionStart and Stop. NEVER runs on the hot path of
UserPromptSubmit. Degrades gracefully: any error exits 0 rather than breaking the
session — an indexer that takes the session down with it is worse than a stale
index.

Stdlib only. No LLM calls, no API key, no server.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import memory_lib as ml
except Exception:
    sys.exit(0)          # nothing to index without the library; never block


def main():
    full = "--rebuild" in sys.argv
    quiet = "--quiet" in sys.argv

    try:
        stats = ml.build_cache(only_changed=not full)
    except Exception as e:
        if not quiet:
            print(json.dumps({"ok": False, "error": str(e)}))
        sys.exit(0)

    # The inverted index is built ALONGSIDE the flat cache, not instead of it: if
    # it ever fails to build or load, recall keeps working through the cache.
    # `build_index` carries its own staleness guard, so the common case (nothing
    # changed) costs a few stat() calls rather than a full rebuild — which
    # matters because this runs on every turn.
    try:
        index_stats = ml.build_index(force=full)
    except Exception as e:
        index_stats = {"index_error": str(e)}

    if not quiet:
        print(json.dumps({"ok": True, **stats, "index": index_stats},
                         ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
