#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
snapshot.py — commits the memory directory to git on its own, at the end of a turn.

Not a gate: the others here refuse things, this one saves. It lives with them
because it closes the same loop — a rule nobody executes and a backup nobody
takes are the same defect wearing different clothes.

Why it exists
-------------
Five hook scripts and five hook registrations were deleted here by accident. What
saved them was a manual copy someone had made six days earlier, because they
happened to remember. It worked by luck.

Versioning the directory only fixes that if the snapshot is taken WITHOUT anyone
remembering. A backup that depends on human memory is the original problem with
an extra step.

Three rules it follows
----------------------
1. **Never breaks the session.** Any error exits quietly. A backup that takes the
   work down with it gets uninstalled, and then it protects nothing.
2. **Never commits a secret.** It scans what would be committed first; on a hit it
   ABORTS and writes which file to the log. A secret that reaches git history
   cannot be taken back out.
3. **Minimum interval.** The Stop hook runs every turn and the session brief is
   rewritten every turn, so committing every time would fill the history with
   noise. It commits at most every `interval_minutes` — except when the change is
   STRUCTURAL (a hook, the settings, the ignore file), which is exactly the case
   that caused the accident and goes immediately.

Configure in `~/.claude/memory-hooks/config.json`:

    "gates": {
      "snapshot": {
        "path": "~/.claude",
        "interval_minutes": 20,
        "structural": ["hooks/", "settings.json", ".gitignore"]
      }
    }

Set up the repository once (the installer offers to do it):

    cd ~/.claude && git init

Registered by install.sh as a Stop hook.
Stdlib only.
"""
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_lib as gl  # noqa: E402

GATE = "snapshot"
DEFAULT_PATH = "~/.claude"
DEFAULT_INTERVAL = 20
DEFAULT_STRUCTURAL = ("hooks/", "settings.json", ".gitignore", ".gitattributes",
                      "commands/", "agents/", "rules/", "gates/")

SECRET_PATTERNS = [
    (re.compile(r"ghp_[A-Za-z0-9]{30,}"), "GitHub token"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{30,}"), "GitHub token (pat)"),
    (re.compile(r"sk-(?!test|ant-api-key|xxx)[A-Za-z0-9_-]{25,}"), "sk- key"),
    (re.compile(r"AIza[0-9A-Za-z_-]{30,}"), "Google key"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "Slack token"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key"),
    (re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{40,}\.[A-Za-z0-9_-]{20,}"),
     "JWT"),
]


def config():
    cfg = gl.gate_config(GATE)
    return (os.path.expanduser(str(cfg.get("path") or DEFAULT_PATH)),
            int(cfg.get("interval_minutes") or DEFAULT_INTERVAL),
            tuple(cfg.get("structural") or DEFAULT_STRUCTURAL))


def git(root, *args):
    return subprocess.run(["git", "-C", root] + list(args), capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          timeout=120)


def minutes_since_last_commit(root):
    result = git(root, "log", "-1", "--format=%ct")
    if result.returncode != 0 or not result.stdout.strip():
        return 10 ** 6
    try:
        return (time.time() - int(result.stdout.strip())) / 60.0
    except ValueError:
        return 10 ** 6


def pending(root):
    result = git(root, "status", "--porcelain", "--untracked-files=all")
    if result.returncode != 0:
        return None
    return [line[3:].strip().strip('"') for line in result.stdout.split("\n")
            if len(line) > 3]


def secrets_in(root, paths):
    """[(path, kind)] for anything that must not be committed."""
    found = []
    for rel in paths:
        full = os.path.join(root, rel.replace("/", os.sep))
        if not os.path.isfile(full):
            continue
        try:
            if os.path.getsize(full) > 5_000_000:
                continue
            with open(full, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        for pattern, kind in SECRET_PATTERNS:
            if pattern.search(text):
                found.append((rel, kind))
                break
    return found


def take_snapshot():
    root, interval, structural = config()
    if not os.path.isdir(os.path.join(root, ".git")):
        return
    changed = pending(root)
    if changed is None:
        gl.log(GATE, "error", root, "git status failed")
        return
    if not changed:
        return

    is_structural = any(c.startswith(structural) for c in changed)
    if not is_structural and minutes_since_last_commit(root) < interval:
        return

    secrets = secrets_in(root, changed)
    if secrets:
        gl.log(GATE, "abort", root, "secret in: " +
               "; ".join("%s (%s)" % (p, k) for p, k in secrets[:5]))
        return

    if git(root, "add", "-A").returncode != 0:
        gl.log(GATE, "error", root, "git add failed")
        return
    staged = git(root, "diff", "--cached", "--name-only").stdout.strip()
    if not staged:
        return
    count = len(staged.split("\n"))
    reason = "structural" if is_structural else "periodic"
    result = git(root, "commit", "-q", "-m",
                 "automatic snapshot (%s) - %d file(s)" % (reason, count))
    if result.returncode != 0:
        gl.log(GATE, "error", root, "git commit failed")
        return
    gl.log(GATE, "commit", root, "%s: %d file(s)" % (reason, count))


if __name__ == "__main__":
    try:
        sys.stdin.buffer.read()          # drain the pipe; nothing here is used
    except Exception:
        pass
    try:
        take_snapshot()
    except Exception as exc:
        gl.log(GATE, "error", "", "%s: %s" % (type(exc).__name__, exc))
    print(json.dumps({"continue": True, "suppressOutput": True}))
