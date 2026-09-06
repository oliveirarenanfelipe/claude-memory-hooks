#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
register_hooks.py — add or remove this project's hooks in ~/.claude/settings.json.

    python tools/register_hooks.py --install
    python tools/register_hooks.py --uninstall
    python tools/register_hooks.py --status

Called by: install.sh, uninstall.sh.

It lives in its own file rather than inside the shell script on purpose. Editing
settings.json is the one destructive thing this installer does, and it belongs
somewhere it can be read, reviewed and run on its own — not buried in a heredoc
inside a shell script.

Safety rules it follows:
  - a timestamped backup of settings.json before any write;
  - atomic write (temp file + replace), so an interrupted run cannot leave a
    half-written settings.json, which would break every hook you have;
  - matching by SCRIPT NAME, so re-running upgrades a registration instead of
    adding a second copy;
  - uninstall touches only this project's hooks, and never your notes.
"""
import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

SCRIPTS = ["memory_config.py", "memory_lib.py", "session_context.py",
           "prompt_memory.py", "auto_brief.py", "reindex_memory.py"]

# (event, script, extra args, timeout in seconds). Order within an event is the
# order the context blocks arrive in.
REGISTRATIONS = [
    ("SessionStart", "reindex_memory.py", " --quiet", 30),
    ("SessionStart", "session_context.py", "", 10),
    ("UserPromptSubmit", "prompt_memory.py", "", 5),
    ("Stop", "reindex_memory.py", " --quiet", 30),
    ("Stop", "auto_brief.py", "", 120),
]


def claude_dir() -> Path:
    return Path(os.environ.get("CLAUDE_HOME") or (Path.home() / ".claude"))


def load_settings(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"settings.json exists but could not be parsed: {e}", file=sys.stderr)
        print("Refusing to overwrite it. Fix or move the file and run again.",
              file=sys.stderr)
        sys.exit(1)


def save_settings(path: Path, settings: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup = path.with_suffix(f".json.bak-{time.strftime('%Y%m%d-%H%M%S')}")
        shutil.copy2(path, backup)
        print(f"  backup: {backup.name}")
    tmp = path.with_suffix(f".json.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    os.replace(tmp, path)


def each_hook(settings: dict):
    for event, groups in (settings.get("hooks") or {}).items():
        for group in groups:
            for hook in group.get("hooks", []):
                yield event, group, hook


def norm(command) -> str:
    return str(command or "").replace("\\", "/")


def install(settings: dict, hooks_dir: Path) -> int:
    hooks = settings.setdefault("hooks", {})
    changed = 0
    for event, script, args, timeout in REGISTRATIONS:
        command = f'python "{hooks_dir / script}"{args}'
        existing = None
        for ev, _group, hook in each_hook(settings):
            if ev == event and script in norm(hook.get("command")):
                existing = hook
                break
        if existing is not None:
            if existing.get("command") != command or existing.get("timeout") != timeout:
                existing["command"] = command
                existing["timeout"] = timeout
                changed += 1
                print(f"  upgraded  {event}/{script}")
            else:
                print(f"  already   {event}/{script}")
            continue
        hooks.setdefault(event, []).append(
            {"hooks": [{"type": "command", "command": command, "timeout": timeout}]})
        changed += 1
        print(f"  added     {event}/{script}")
    return changed


def uninstall(settings: dict) -> int:
    hooks = settings.get("hooks") or {}
    removed = 0
    for event in list(hooks):
        groups = []
        for group in hooks[event]:
            keep = []
            for hook in group.get("hooks", []):
                if any(s in norm(hook.get("command")) for s in SCRIPTS):
                    removed += 1
                    name = norm(hook.get("command")).rsplit("/", 1)[-1]
                    print(f"  removed   {event}/{name}")
                else:
                    keep.append(hook)
            if keep:
                group["hooks"] = keep
                groups.append(group)
        if groups:
            hooks[event] = groups
        else:
            del hooks[event]
    return removed


def status(settings: dict) -> int:
    found = 0
    for event, _group, hook in each_hook(settings):
        command = norm(hook.get("command"))
        if any(s in command for s in SCRIPTS):
            found += 1
            print(f"  {event:16} timeout={hook.get('timeout')}  "
                  f"{command.rsplit('/', 1)[-1]}")
    if not found:
        print("  none of this project's hooks are registered")
    return found


def main():
    parser = argparse.ArgumentParser(description="Register or remove the hooks.")
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()

    base = claude_dir()
    settings_path = base / "settings.json"
    settings = load_settings(settings_path)

    if args.status or not (args.install or args.uninstall):
        print(f"settings: {settings_path}")
        status(settings)
        return 0

    if args.install:
        changed = install(settings, base / "hooks")
        if changed:
            save_settings(settings_path, settings)
        print(f"  {changed} registration(s) written")
    else:
        removed = uninstall(settings)
        if removed:
            save_settings(settings_path, settings)
        print(f"  {removed} registration(s) removed")
        print("  your notes and session briefs were not touched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
