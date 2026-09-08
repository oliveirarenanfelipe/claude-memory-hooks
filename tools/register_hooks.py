#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
register_hooks.py — add or remove this project's hooks in ~/.claude/settings.json.

    python tools/register_hooks.py --install --level engine
    python tools/register_hooks.py --install --level full
    python tools/register_hooks.py --uninstall
    python tools/register_hooks.py --status

Called by: install.sh, uninstall.sh.

Two levels, because the two halves of this project answer different questions:

  engine  the memory: remember across sessions, recall what is relevant.
  full    the memory PLUS the method: gates that refuse, and an automatic
          snapshot of the memory directory.

`full` changes how your sessions behave — it will refuse actions. That is the
point, and it is also why it is opt-in rather than the default.

It lives in its own file rather than inside the shell script on purpose. Editing
settings.json is the one destructive thing this installer does, and it belongs
somewhere it can be read, reviewed and run on its own — not buried in a heredoc
inside a shell script. That is not a style preference: a heredoc holding a script
is exactly how five hook scripts got deleted here.

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

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ENGINE_SCRIPTS = ["memory_config.py", "memory_lib.py", "session_context.py",
                  "prompt_memory.py", "auto_brief.py", "reindex_memory.py"]
GATE_SCRIPTS = ["gate_lib.py", "no_orphan_files.py", "destructive_bash.py",
                "project_boundary.py", "context_budget.py", "snapshot.py",
                "redact_secrets.py", "question_is_analysis.py"]
ALL_SCRIPTS = ENGINE_SCRIPTS + GATE_SCRIPTS

# (event, matcher or None, folder, script, extra args, timeout seconds)
ENGINE_HOOKS = [
    ("SessionStart", None, "hooks", "reindex_memory.py", " --quiet", 30),
    ("SessionStart", None, "hooks", "session_context.py", "", 10),
    ("UserPromptSubmit", None, "hooks", "prompt_memory.py", "", 5),
    ("Stop", None, "hooks", "reindex_memory.py", " --quiet", 30),
    ("Stop", None, "hooks", "auto_brief.py", "", 120),
]
GATE_HOOKS = [
    ("PreToolUse", "Bash", "gates", "destructive_bash.py", "", 15),
    ("PreToolUse", "Write", "gates", "no_orphan_files.py", "", 15),
    ("PreToolUse", "Edit|Write", "gates", "project_boundary.py", "", 15),
    ("PreToolUse", "Edit|Write", "gates", "context_budget.py", "", 15),
    ("Stop", None, "gates", "snapshot.py", "", 120),
    # PostToolUse, not PreToolUse: it rewrites the RESULT, so it has to run
    # after the tool, and it never blocks.
    ("PostToolUse", None, "gates", "redact_secrets.py", "", 15),
    # Matches the ACTION tools only: reading and searching must never be
    # blocked, because reading is exactly what a question deserves.
    ("PreToolUse", "Edit|Write|Bash", "gates", "question_is_analysis.py", "", 15),
]


def claude_dir():
    return os.environ.get("CLAUDE_HOME") or os.path.join(os.path.expanduser("~"),
                                                         ".claude")


def load_settings(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {}
    except Exception as exc:
        print("settings.json exists but could not be parsed: %s" % exc,
              file=sys.stderr)
        print("Refusing to overwrite it. Fix or move the file and run again.",
              file=sys.stderr)
        sys.exit(1)


def save_settings(path, settings):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    if os.path.exists(path):
        backup = "%s.bak-%s" % (path, time.strftime("%Y%m%d-%H%M%S"))
        shutil.copy2(path, backup)
        print("  backup: %s" % os.path.basename(backup))
    tmp = "%s.%d.tmp" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(settings, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path)


def each_hook(settings):
    for event, groups in (settings.get("hooks") or {}).items():
        for group in groups:
            for hook in group.get("hooks", []):
                yield event, group, hook


def norm(command):
    return str(command or "").replace("\\", "/")


def wanted(level):
    return ENGINE_HOOKS + (GATE_HOOKS if level == "full" else [])


def install(settings, base, level):
    hooks = settings.setdefault("hooks", {})
    changed = 0
    for event, matcher, folder, script, args, timeout in wanted(level):
        command = 'python "%s"%s' % (os.path.join(base, folder, script), args)
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
                print("  upgraded  %s/%s" % (event, script))
            else:
                print("  already   %s/%s" % (event, script))
            continue
        group = {"hooks": [{"type": "command", "command": command,
                            "timeout": timeout}]}
        if matcher:
            group["matcher"] = matcher
        hooks.setdefault(event, []).append(group)
        changed += 1
        print("  added     %s/%s" % (event, script))
    return changed


def uninstall(settings):
    hooks = settings.get("hooks") or {}
    removed = 0
    for event in list(hooks):
        groups = []
        for group in hooks[event]:
            keep = []
            for hook in group.get("hooks", []):
                command = norm(hook.get("command"))
                if any(s in command for s in ALL_SCRIPTS):
                    removed += 1
                    print("  removed   %s/%s" % (event, command.rsplit("/", 1)[-1]))
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


def status(settings):
    found = 0
    for event, _group, hook in each_hook(settings):
        command = norm(hook.get("command"))
        if any(s in command for s in ALL_SCRIPTS):
            found += 1
            print("  %-16s timeout=%-4s %s" % (event, hook.get("timeout"),
                                               command.rsplit("/", 1)[-1]))
    if not found:
        print("  none of this project's hooks are registered")
    return found


def main():
    parser = argparse.ArgumentParser(description="Register or remove the hooks.")
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--level", choices=("engine", "full"), default="engine")
    args = parser.parse_args()

    base = claude_dir()
    settings_path = os.path.join(base, "settings.json")
    settings = load_settings(settings_path)

    if args.status or not (args.install or args.uninstall):
        print("settings: %s" % settings_path)
        status(settings)
        return 0

    if args.install:
        changed = install(settings, base, args.level)
        if changed:
            save_settings(settings_path, settings)
        print("  %d registration(s) written  (level: %s)" % (changed, args.level))
        if args.level == "full":
            print("  the gates will now REFUSE some actions — that is the point")
    else:
        removed = uninstall(settings)
        if removed:
            save_settings(settings_path, settings)
        print("  %d registration(s) removed" % removed)
        print("  your notes and session briefs were not touched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
