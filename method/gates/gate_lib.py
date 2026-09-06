#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gate_lib.py — the shared contract every gate in this folder follows.

A gate is a Claude Code `PreToolUse` hook that can REFUSE an action. Not warn —
refuse. That distinction is the whole point of this folder, and it was paid for:
a rule written in a document had been in place for nineteen days, in the exact
words needed, and it did not stop the mistake it described. A gate that blocks
would have.

Called by: every other `*.py` in this folder, and `tests/test_gates.py`.

The four rules a gate here obeys
--------------------------------
1. **Read stdin as bytes, decode UTF-8 explicitly.** On Windows the console
   locale is cp1252 while the hook payload arrives as UTF-8. `json.load(sys.stdin)`
   silently produces mojibake, the target path never matches, and the gate
   returns quietly as if everything were fine. A gate that is inert and looks
   active is worse than no gate — and two gates shipped that way here.

2. **Write stdout as UTF-8 explicitly.** Same reason, opposite direction: a
   refusal message containing an accent or an arrow raises UnicodeEncodeError,
   the hook exits non-zero with no output, and the action goes through. This was
   caught by a test, not by reading — the gate that motivated this whole folder
   died the first time it tried to refuse.

3. **Never raise.** Any unexpected error means the gate steps aside. A gate that
   breaks the session it was meant to protect gets uninstalled within a day, and
   then it protects nothing.

4. **Say what to do next.** A refusal that does not name the way forward is an
   obstacle, and obstacles get switched off. Every message here ends with a
   concrete next step.

Stdlib only.
"""
import io
import json
import os
import sys
import tempfile
import time

LOG = os.path.join(os.path.expanduser("~"), ".claude", "gates.log")


def stdout_utf8():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def read_event():
    """The hook payload, or None. Never raises. See rule 1."""
    try:
        return json.loads(sys.stdin.buffer.read().decode("utf-8", "replace"))
    except Exception:
        return None


def tool_name(event):
    return (event or {}).get("tool_name") or ""


def tool_input(event):
    return (event or {}).get("tool_input") or {}


def target_path(event):
    return tool_input(event).get("file_path") or ""


def bash_command(event):
    return tool_input(event).get("command") or ""


def log(gate, decision, target, reason):
    """Record only. A logger that fails must never bring a guard down."""
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with io.open(LOG, "a", encoding="utf-8") as fh:
            fh.write("\t".join([time.strftime("%Y-%m-%d %H:%M:%S"), gate,
                                decision, str(target)[:120],
                                str(reason).replace("\n", " ")[:150]]) + "\n")
    except Exception:
        pass


def deny(gate, lines, target=""):
    """Refuse the action, with the reason and the way forward. See rules 2 and 4."""
    stdout_utf8()
    log(gate, "deny", target, lines[0] if lines else "")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "\n".join(lines)}}, ensure_ascii=False))


def already_flagged(gate, session_id, key):
    """True when this gate already stopped this exact target in this session.

    Used by the gates whose job is to make something VISIBLE rather than
    forbidden: they interrupt once, and a repeat goes through. That costs the
    person one sentence explaining why — which is the point — without turning a
    guard into a toll on whoever is doing the right thing.

    NOT used by gates protecting something irreversible. Those never yield to
    repetition; they require an explicit written marker instead. A guard on a
    destructive action that gives up on the second try is decoration.
    """
    marker = os.path.join(tempfile.gettempdir(),
                          "gate_%s_%s.json" % (gate, session_id or "x"))
    seen = []
    if os.path.exists(marker):
        try:
            with io.open(marker, encoding="utf-8") as fh:
                seen = json.load(fh)
        except Exception:
            seen = []
    if key in seen:
        return True
    seen.append(key)
    try:
        with io.open(marker, "w", encoding="utf-8") as fh:
            json.dump(seen, fh)
    except Exception:
        pass
    return False


def load_config():
    """`~/.claude/memory-hooks/config.json`, or {}. Never raises."""
    path = os.path.join(os.path.expanduser("~"), ".claude",
                        "memory-hooks", "config.json")
    try:
        with io.open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def gate_config(name):
    """The `gates.<name>` section of the config, or {}."""
    return (load_config().get("gates") or {}).get(name) or {}


def run(gate_name, handler):
    """Boilerplate every gate shares: read, dispatch, never raise. See rule 3."""
    event = read_event()
    if event is None:
        return
    try:
        handler(event)
    except Exception as exc:
        log(gate_name, "error", "", "%s: %s" % (type(exc).__name__, exc))
        return
