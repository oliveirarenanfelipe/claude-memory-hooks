#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
project_boundary.py — interrupts a write into a project other than the one the
session is open on.

The question that produced it
----------------------------
"This session is on project A — why are you working on project B's backlog?"

The investigation found two things, and only the second was a defect:

  1. SEEING another project's items is deliberate. A session-start hook injects a
     cross-project summary on purpose, precisely so nothing gets forgotten
     because it lives in a folder nobody opened. That is the feature.

  2. ACTING on them had no brake. Nothing in the system marked the boundary. The
     injected text names the project but not whether it is yours to act on; the
     written rules never mentioned scope; and none of the gates looked at which
     project a file belonged to. Measured that day: from a single session, files
     were written in FIVE different projects, and nothing stopped any of it.

What it does — and does not do
------------------------------
It does not forbid. It makes the crossing VISIBLE. The write is refused ONCE,
naming the owning project; repeat and it goes through. So a legitimate
instruction to work across projects costs one sentence saying why — which the
person sees in the conversation, instead of it happening silently.

A guard that charges a toll on whoever is doing the right thing becomes a tax.
This one charges a sentence.

Deliberately NOT gated (cross-cutting by design):
  - paths listed in `shared_paths`
  - the Claude home directory outside `projects/` — hooks, rules, commands are global
  - temp and scratch directories: a draft is not a delivery

Known limit, declared rather than hidden: the separation is only as good as the
project detection. Two sibling folders that resolve to the same slug will not be
separated from each other. That is a property of how projects are named, not
something this gate can fix on its own.

It REUSES the engine's project resolver rather than implementing its own. A
second implementation drifts from the first in silence, and then the indexer and
the boundary disagree about which project a file belongs to — a failure that has
already cost this project a hundred and forty-five notes being scored as foreign
inside their own project.

Configure in `~/.claude/memory-hooks/config.json`:

    "gates": {
      "project_boundary": {
        "project_roots": ["~/code"],
        "shared_paths": ["~/code/_shared"]
      }
    }

Registered by install.sh as a PreToolUse hook (matcher: Edit|Write).
Stdlib only.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                "engine", "hooks"))
sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "hooks"))

import gate_lib as gl  # noqa: E402

GATE = "project_boundary"
CLAUDE_HOME = os.path.join(os.path.expanduser("~"), ".claude")
MEMORY_ROOT = os.path.normcase(os.path.join(CLAUDE_HOME, "projects"))


def _config():
    cfg = gl.gate_config(GATE)
    roots = [os.path.normcase(os.path.abspath(os.path.expanduser(str(p))))
             for p in (cfg.get("project_roots") or [])]
    free = [os.path.normcase(os.path.abspath(os.path.expanduser(str(p))))
            for p in (cfg.get("shared_paths") or [])]
    free.append(os.path.normcase(tempfile.gettempdir()))
    return roots, free


def _resolver():
    """The engine's project resolver, or None when it is not installed."""
    try:
        import memory_config
        return memory_config
    except Exception:
        return None


def owner_of(path, roots, free, resolver):
    """Slug of the project that owns a path, or '' when it is cross-cutting."""
    normalised = os.path.normcase(os.path.abspath(path))
    if any(normalised.startswith(f) for f in free):
        return ""
    if normalised.startswith(MEMORY_ROOT):
        rest = normalised[len(MEMORY_ROOT):].lstrip("\\/")
        folder = rest.split(os.sep)[0] if rest else ""
        return resolver.slug_from_dirname(folder) if folder else ""
    if normalised.startswith(os.path.normcase(CLAUDE_HOME)):
        return ""                      # hooks, rules, commands: the mind is global
    for root in roots:
        if normalised.startswith(root):
            return resolver.detect_project(os.path.dirname(normalised) or normalised)
    return ""


def handle(event):
    if gl.tool_name(event) not in ("Edit", "Write", "NotebookEdit"):
        return
    path = gl.target_path(event)
    if not path:
        return

    resolver = _resolver()
    if resolver is None:
        return                         # without the resolver, invent no verdict

    roots, free = _config()
    owner = owner_of(path, roots, free, resolver)
    if not owner:
        return                         # cross-cutting: let it through

    session_project = resolver.detect_project(event.get("cwd") or os.getcwd())
    if not session_project or session_project == owner:
        return

    key = os.path.normcase(os.path.abspath(path))
    if gl.already_flagged(GATE, event.get("session_id"), key):
        return                         # flagged once; the repeat goes through

    gl.deny(GATE, [
        "STOP — this file belongs to project **%s**, and the session is open on "
        "**%s**." % (owner, session_project),
        "",
        "  file: %s" % path,
        "",
        "Seeing another project's work is deliberate — the session-start summary "
        "puts it in front of you on purpose. But that is a NOTICE, not a work "
        "queue: acting on an item means opening its own project, which loads its "
        "decisions, its rules and its open work. None of that is on the table "
        "from here.",
        "",
        "If writing HERE really is right — an explicit instruction, or a "
        "cross-cutting piece — say in one sentence why, and repeat: the second "
        "attempt on the same file goes through.",
    ], path)


if __name__ == "__main__":
    gl.run(GATE, handle)
