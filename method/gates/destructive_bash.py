#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
destructive_bash.py — refuses a shell command that could destroy the memory, and
refuses the shell mistake that causes it.

The accident this was written for
---------------------------------
Someone was WRITING an uninstall script — the content was data, text destined for
a file. It was passed through a bash heredoc, and inside that text there was
another heredoc using THE SAME delimiter. The inner one closed the outer one, and
from that line on the shell stopped treating the text as content and started
executing it as commands, pointed at the real home directory.

  - 5 hook scripts deleted
  - 5 hook registrations stripped from settings.json
  - the search index, the cache and the recall log deleted

What made it worth turning into a gate: on that same day the other guards refused
seven actions — every one of them a harmless file creation through the Write tool
— and zero through Bash. The guards watched the safe tool and left the dangerous
one open.

Two things it refuses
---------------------
1. A destructive command touching a protected directory (delete, move,
   overwrite, reset).
2. A nested heredoc reusing the same delimiter — the exact leak above.

Sequential heredocs sharing a delimiter are NOT refused: that pattern works and
is common. Only nesting is.

The deliberate override
-----------------------
Put `# GATE-OK: <reason>` in the command. Chosen on purpose: the failure mode
here is ACCIDENTAL EXECUTION, and leaked text never carries that marker.

Unlike the other gates in this folder, **repeating the command does not get you
through**. A guard on something irreversible that yields on the second attempt is
decoration.

Configure in `~/.claude/memory-hooks/config.json`:

    "gates": {
      "destructive_bash": {
        "protect": ["~/.claude", "~/notes"],
        "marker": "# GATE-OK:"
      }
    }

Registered by install.sh as a PreToolUse hook (matcher: Bash).
Stdlib only.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_lib as gl  # noqa: E402

GATE = "destructive_bash"
DEFAULT_MARKER = "# GATE-OK:"
DEFAULT_PROTECT = ["~/.claude"]

# `cp` is here because overwriting a script is as destructive as deleting it —
# restoring from a backup should be deliberate too.
DESTRUCTIVE = [
    (r"\brm\b", "rm"),
    (r"\bmv\b", "mv"),
    (r"\bcp\b", "cp"),
    (r"\bdd\b", "dd"),
    (r"\bshred\b", "shred"),
    (r"\btruncate\b", "truncate"),
    (r"\brmdir\b", "rmdir"),
    (r"\bunlink\s*\(", "unlink()"),
    (r"\bos\.remove\b", "os.remove"),
    (r"\bos\.replace\b", "os.replace"),
    (r"\bshutil\.rmtree\b", "shutil.rmtree"),
    (r"\bshutil\.move\b", "shutil.move"),
    # The real command carries options in between — `git -C <dir> reset --hard`.
    # Written with the words adjacent this never matched. Caught by the test, not
    # by reading the code.
    (r"\bgit\b[^\n;|&]*\breset\s+--hard\b", "git reset --hard"),
    (r"\bgit\b[^\n;|&]*\bclean\b\s+-", "git clean"),
    (r"\bgit\b[^\n;|&]*\bcheckout\s+--\s", "git checkout --"),
    (r"\bgit\b[^\n;|&]*\brestore\b", "git restore"),
    (r"\bwrite_text\s*\(", "write_text()"),
    (r"open\s*\([^)]*[\"']w[\"']", "open(...,'w')"),
    # A shell redirect overwrites. This list is only consulted once the command
    # has already been found to touch a protected path, so a bare `>` is safe to
    # match here — it cannot fire on `echo x > /tmp/y`.
    # The earlier version of this pattern had the protected directory name baked
    # into it, which meant it silently stopped matching for anyone whose
    # protected path was named something else. Caught by the test, not by review.
    (r"(?<![0-9<])>{1,2}\s*[^\s|&;<>]", "redirect (>) overwriting a file"),
]

HEREDOC = re.compile(r"<<-?\s*([\"']?)([A-Za-z_][A-Za-z0-9_]*)\1")


def protected_patterns():
    """[(regex, label)] — matches the tail of each protected path.

    Matching the last path segment rather than the full path is deliberate: the
    command usually builds the path from a variable (`$HOME/.claude`,
    `${CLAUDE_HOME}`), so the literal full path is rarely present. The segment is.
    """
    raw = gl.gate_config(GATE).get("protect") or DEFAULT_PROTECT
    out = []
    for entry in raw:
        expanded = os.path.expanduser(str(entry))
        tail = os.path.basename(expanded.rstrip("/\\")) or expanded
        out.append((re.compile(re.escape(tail) + r"\b", re.I), entry))
    return out


def nested_same_delimiter(command):
    """The offending delimiter, or None.

    Walks the command the way bash does. While heredoc D is open, lines are
    CONTENT until a line equal to D. If an opener for D itself shows up inside
    that content, that is the trap: nesting was intended, bash closed early, and
    the rest of the text became commands.

    Sequential heredocs sharing a name are not flagged — that works.
    """
    open_delim = None
    for line in command.split("\n"):
        if open_delim is None:
            match = HEREDOC.search(line)
            if match:
                open_delim = match.group(2)
            continue
        if line.strip() == open_delim:
            open_delim = None
            continue
        match = HEREDOC.search(line)
        if match and match.group(2) == open_delim:
            return open_delim
    return None


def found_verbs(command):
    return [name for pattern, name in DESTRUCTIVE if re.search(pattern, command)]


def analyse(command):
    """[(title, detail, fix)] — empty means it may go through."""
    marker = gl.gate_config(GATE).get("marker") or DEFAULT_MARKER
    if marker in command:
        return []
    reasons = []

    delimiter = nested_same_delimiter(command)
    if delimiter:
        reasons.append((
            "NESTED HEREDOC reusing the delimiter `%s`." % delimiter,
            "The inner `%s` CLOSES the outer one. Everything after it stops being "
            "content and is executed as a command. That is how five hook scripts "
            "and five registrations were deleted." % delimiter,
            "Content that itself contains shell or python goes through the WRITE "
            "tool, never a heredoc. If it must be a heredoc, use distinct "
            "delimiters and never nest them."))

    for pattern, label in protected_patterns():
        if not pattern.search(command):
            continue
        verbs = found_verbs(command)
        if verbs:
            reasons.append((
                "DESTRUCTIVE command touching `%s`: %s." % (label, ", ".join(verbs)),
                "That directory holds the hooks, the memories, the briefs and the "
                "settings. A mistake there has no undo, and the newest backup may "
                "be days old.",
                "If this is intentional, repeat the command with `%s <reason>` at "
                "the end. Repeating WITHOUT the marker does not get through."
                % marker))
        break
    return reasons


def handle(event):
    if gl.tool_name(event) != "Bash":
        return
    command = gl.bash_command(event)
    if not command:
        return
    reasons = analyse(command)
    if not reasons:
        return
    lines = ["STOP — this shell command could destroy the memory.", ""]
    for title, detail, fix in reasons:
        lines += ["  - " + title, "    " + detail, "    -> " + fix, ""]
    lines.append("This gate does NOT yield on a second attempt, unlike the others "
                 "here. Use the marker, or change the command.")
    gl.deny(GATE, lines)


if __name__ == "__main__":
    gl.run(GATE, handle)
