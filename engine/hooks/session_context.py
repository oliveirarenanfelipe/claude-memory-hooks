#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
session_context.py — SessionStart hook: inject the last session's brief.

Claude opens already knowing the project, what was done last time, what the next
step is and what is blocked. You just continue.

Optionally runs `git pull` first, for people who sync their notes between
machines (config: `sync`). Off by default.

Registered by install.sh as a SessionStart hook (10s timeout).

Stdlib only. No LLM calls, no API key, no server.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory_config as cfgmod          # noqa: E402


def read_brief(cwd: str, slug: str) -> str:
    if not slug:
        return ""
    path = cfgmod.briefs_dir_for(cwd) / f"{slug}.md"
    if not path.exists():
        return ""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2].strip()
    return content


def sync_notes(cfg: dict) -> str:
    """Pull a notes repo at session start. Returns a WARNING string, or "".

    Why the failure is reported instead of swallowed: a pull that fails silently
    is worse than no pull at all. Measured here — one diverged branch made every
    pull fail for sixteen days with its return code unread, the machine fell 67
    commits behind, and a later session confidently concluded "nothing new has
    arrived" while reading a dead copy. `--rebase --autostash` gets past a local
    commit and a dirty tree; the warning gets past the silence.
    """
    sync = cfg.get("sync") or {}
    if not sync.get("enabled"):
        return ""
    path = Path(str(sync.get("path", "")).strip())
    try:
        if not path.is_dir() or not (path / ".git").is_dir():
            return ""
        import subprocess
        remote = subprocess.run(["git", "-C", str(path), "remote"],
                                capture_output=True, text=True, timeout=5)
        if remote.returncode != 0 or not remote.stdout.strip():
            return ""
        r = subprocess.run(
            ["git", "-C", str(path), "-c", "rebase.autoStash=true",
             "pull", "--rebase", "--quiet"],
            capture_output=True, text=True, timeout=int(sync.get("timeout", 60)))
        if r.returncode != 0:
            err = (r.stderr or r.stdout or "").strip().splitlines()
            err = err[-1] if err else f"exit {r.returncode}"
            return ("## ⚠️ notes sync FAILED\n"
                    f"`git pull` in `{path}` did not run: `{err}`\n"
                    "Anything written from another machine is invisible here. "
                    "Fix this before trusting what you read.")
        return ""
    except Exception as e:
        return (f"## ⚠️ notes sync could not run ({type(e).__name__})\n"
                "Recent notes may be missing on this machine.")


def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except Exception:
        print(json.dumps({"continue": True}))
        sys.exit(0)

    cfg = cfgmod.load()
    warning = sync_notes(cfg)

    cwd = data.get("cwd", "")
    slug = cfgmod.detect_project(cwd, cfg)
    brief = read_brief(cwd, slug)

    if not brief and not warning:
        print(json.dumps({"continue": True}))
        sys.exit(0)

    parts = []
    if warning:
        parts.append(warning)
    if brief:
        parts.append(f"## Last session — {slug}\n\n{brief}")

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "\n\n".join(parts),
    }}))


if __name__ == "__main__":
    main()
