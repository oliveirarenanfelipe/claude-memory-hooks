#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
no_orphan_files.py — refuses the first attempt to create a new code file, and
asks three questions.

The habit it exists to break
----------------------------
Building something new feels like progress, so it wins over the duller work of
finding what already does the job. The result is a codebase where the twenty-ninth
helper does what the fourth one already did, and a folder of tools that were
evaluated, approved, and never called by anything.

The three questions:

  1. Does something already do this? If so, use it or extend it.
  2. Who will CALL this? Name the file. Without a caller in the same commit it is
     not a delivery, it is an orphan.
  3. Does a tool you already approved solve it?

Why a gate and not a checklist
------------------------------
The trigger is the ACTION, not a word. A checklist in a document only fires when
someone remembers to classify the situation as "choosing a tool" — and the moment
you are about to write file twenty-nine is exactly the moment you have not
classified it that way. The gate arrives at that second, every time, without
depending on anyone's memory.

It interrupts ONCE per file. Answer the three questions and repeat the same
creation: the second attempt goes through. A guard that blocks the right work
forever becomes a tax, and taxes get uninstalled.

Configure in `~/.claude/memory-hooks/config.json`:

    "gates": {
      "no_orphan_files": {
        "extensions": [".py", ".js", ".ts", ".sh"],
        "ignore": ["scratch", "/tmp/", "node_modules", "vendor"],
        "search_roots": ["."]
      }
    }

Registered by install.sh as a PreToolUse hook (matcher: Write).
Stdlib only.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_lib as gl  # noqa: E402

GATE = "no_orphan_files"

DEFAULT_EXTENSIONS = (".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".rb", ".go",
                      ".rs", ".java", ".sh", ".sql", ".ps1")
# Scratch space is not a delivery, so it is not gated. Being generous here is
# what keeps the gate from becoming a tax on ordinary work.
DEFAULT_IGNORE = ("scratch", "/tmp/", "\\temp\\", "/temp/", "node_modules",
                  "vendor", "/build/", "/dist/", "__pycache__", "/.git/")


def config():
    cfg = gl.gate_config(GATE)
    return (tuple(cfg.get("extensions") or DEFAULT_EXTENSIONS),
            tuple(cfg.get("ignore") or DEFAULT_IGNORE),
            tuple(cfg.get("search_roots") or (".",)))


def is_ignored(path, ignore):
    """True when the path sits inside an exempt directory.

    A bare name matches a whole PATH SEGMENT, never a substring. That
    distinction is the difference between a working gate and one that is
    silently off: matching substrings, the exemption for `scratch` also
    exempted every path containing the word — a folder named `scratchpad`
    anywhere in the path disabled the gate entirely, and nothing said so.
    Found by running the suite from a checkout that happened to live under
    such a folder.

    A fragment containing a slash is still matched as a sub-path, so you can
    write `src/generated` and mean it.
    """
    normalised = path.replace("\\", "/").lower()
    segments = [s for s in normalised.split("/") if s]
    for fragment in ignore:
        frag = fragment.replace("\\", "/").strip("/").lower()
        if not frag:
            continue
        if "/" in frag:
            if ("/" + frag + "/") in ("/" + "/".join(segments) + "/"):
                return True
        elif frag in segments:
            return True
    return False


def is_gated(path, extensions, ignore):
    if not path:
        return False
    if is_ignored(path, ignore):
        return False
    return path.lower().endswith(tuple(e.lower() for e in extensions))


def similar_names(path, roots, limit=6):
    """Files whose name resembles the one being created.

    Deliberately crude — a shared word in the filename. The goal is not to decide
    anything, it is to put the candidates in front of the person at the moment
    they would otherwise not look. A smarter search that runs slowly would miss
    the hook timeout, and the gate would then be silently off.
    """
    stem = os.path.splitext(os.path.basename(path))[0].lower()
    parts = [p for p in stem.replace("-", "_").split("_") if len(p) >= 4]
    if not parts:
        return []
    found = []
    for root in roots:
        if not os.path.isdir(root):
            continue
        for base, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs
                       if d not in (".git", "node_modules", "__pycache__",
                                    "venv", ".venv", "dist", "build")]
            for name in files:
                low = name.lower()
                if low == os.path.basename(path).lower():
                    continue
                if any(p in low for p in parts):
                    found.append(os.path.join(base, name))
                    if len(found) >= limit:
                        return found
    return found


def handle(event):
    if gl.tool_name(event) not in ("Write", "NotebookEdit"):
        return
    path = gl.target_path(event)
    extensions, ignore, roots = config()
    if not is_gated(path, extensions, ignore):
        return
    if os.path.exists(path):
        return                      # editing something that exists is not a new piece
    if gl.already_flagged(GATE, event.get("session_id"), os.path.abspath(path)):
        return                      # asked once; the repeat goes through

    lines = [
        "STOP before creating `%s`." % os.path.basename(path),
        "",
        "This is the moment a new piece is born with nothing calling it.",
        "Answer these three in your reply, then repeat the creation — the second "
        "attempt goes through.",
        "",
        "  1. Does something already do this? If yes, use it or extend it.",
        "  2. Who will CALL this piece? Name the file. Without a caller in the "
        "same commit it is not a delivery, it is an orphan.",
        "  3. Does a tool you already approved solve it?",
    ]
    nearby = similar_names(path, roots)
    if nearby:
        lines += ["", "Files here with a similar name:"]
        lines += ["  - " + n for n in nearby]
    gl.deny(GATE, lines, path)


if __name__ == "__main__":
    gl.run(GATE, handle)
