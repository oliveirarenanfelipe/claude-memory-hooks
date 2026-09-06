#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
context_budget.py — refuses an edit that pushes an always-loaded instruction file
past its size budget.

Why a file like this needs a guard at all
-----------------------------------------
The instruction file (CLAUDE.md, or whatever your setup always loads) is re-read
on EVERY request, in every project. Its cost is not paid once — it is paid on
every single turn, forever, out of the one budget everything else competes for.

That cost is invisible while you write. Each addition is small and each one is
justified. Nobody ever decides to make the file huge; it becomes huge one
reasonable line at a time. Measured in the setup this comes from: a section that
described itself as "a short index, one line per item" had grown to a hundred and
forty-eight thousand characters and held a hundred and twelve items that were
already closed — and it was being sent on every request of every project.

There is a second, worse effect. A file that long stops being read carefully — by
people and by models alike. Past a certain size, adding a rule makes the rules
already in there LESS likely to be followed. The budget is not really about
tokens; it is about whether the document still works.

What it does
------------
Refuses an edit that would push the watched file past `max_kb`, and refuses a
line longer than `max_line_chars` inside a section you declared to be an index.
The message says where the detail belongs instead.

Interrupts once per file per session: fix it and repeat, and it goes through.

Configure in `~/.claude/memory-hooks/config.json`:

    "gates": {
      "context_budget": {
        "files": [
          { "path": "~/code/CLAUDE.md",
            "max_kb": 40,
            "index_sections": ["## Open items"],
            "max_line_chars": 180,
            "detail_goes_to": "the per-project notes" }
        ]
      }
    }

With no configuration this gate does nothing at all — it has no default file,
because guessing which document is sacred to you would be worse than silence.

Registered by install.sh as a PreToolUse hook (matcher: Edit|Write).
Stdlib only.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_lib as gl  # noqa: E402

GATE = "context_budget"


def watched_files():
    return gl.gate_config(GATE).get("files") or []


def resulting_text(path, tool_input):
    """The text the file would hold after this edit, or None if unknown."""
    content = tool_input.get("content")
    if content is not None:
        return content                     # Write: the whole file
    old = tool_input.get("old_string")
    new = tool_input.get("new_string")
    if old is None or new is None:
        return None
    try:
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            current = fh.read()
    except OSError:
        return None
    if old not in current:
        return None                        # cannot tell; do not invent a verdict
    return current.replace(old, new, 1)


def section_of(text, position, headings):
    """The declared index section a position falls inside, or None."""
    before = text[:position]
    best = None
    for heading in headings:
        index = before.rfind(heading)
        if index == -1:
            continue
        following = text.find("\n#", index + len(heading))
        if following == -1 or following > position:
            if best is None or index > best[1]:
                best = (heading, index)
    return best[0] if best else None


def long_lines_in_index(text, headings, limit):
    """[(section, line)] for index lines too long to be index lines."""
    if not headings or limit <= 0:
        return []
    offenders = []
    position = 0
    for line in text.split("\n"):
        stripped = line.strip()
        if len(stripped) > limit and stripped.startswith(("-", "*", "|")):
            section = section_of(text, position, headings)
            if section:
                offenders.append((section, stripped))
        position += len(line) + 1
    return offenders


def handle(event):
    if gl.tool_name(event) not in ("Edit", "Write"):
        return
    path = gl.target_path(event)
    if not path:
        return
    target = os.path.normcase(os.path.abspath(path))

    for entry in watched_files():
        watched = os.path.normcase(os.path.abspath(
            os.path.expanduser(str(entry.get("path", "")))))
        if watched != target:
            continue

        text = resulting_text(path, gl.tool_input(event))
        if text is None:
            return

        max_kb = float(entry.get("max_kb", 0) or 0)
        headings = entry.get("index_sections") or []
        max_line = int(entry.get("max_line_chars", 0) or 0)
        where = entry.get("detail_goes_to") or "a file that loads on demand"

        size_kb = len(text.encode("utf-8")) / 1024.0
        problems = []
        if max_kb and size_kb > max_kb:
            problems.append(
                "the file would reach **%.1f KB**, over the budget of %.0f KB"
                % (size_kb, max_kb))
        for section, line in long_lines_in_index(text, headings, max_line)[:3]:
            problems.append(
                "a line under `%s` has %d characters (limit %d): `%s...`"
                % (section, len(line), max_line, line[:60]))

        if not problems:
            return
        if gl.already_flagged(GATE, event.get("session_id"), target):
            return

        gl.deny(GATE, [
            "STOP — this edit pushes an always-loaded file past its budget.",
            "",
            "  file: %s" % path,
            "",
            "What did not pass:",
        ] + ["  - " + p for p in problems] + [
            "",
            "This file is re-read on EVERY request, in every project — its cost is "
            "paid on every turn, forever. And past a certain size it stops being "
            "read carefully, so adding a rule makes the existing rules LESS likely "
            "to be followed.",
            "",
            "Put the detail in %s and leave a one-line pointer here. Then repeat: "
            "the second attempt goes through." % where,
        ], path)
        return


if __name__ == "__main__":
    gl.run(GATE, handle)
