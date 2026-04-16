#!/usr/bin/env python3
"""
session_context.py — SessionStart hook
Injects the last session brief into Claude's context at the start of every session.
Claude knows where you left off without you having to explain.

No LLM calls. No API key needed. No external dependencies.
"""
import json
import sys
import subprocess
from pathlib import Path

HOME = Path.home()


def get_project_slug(cwd: str) -> str:
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=cwd, capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            remote = result.stdout.strip()
            name = remote.rstrip("/").split("/")[-1].replace(".git", "")
            if name:
                return name.lower()
    except Exception:
        pass
    return Path(cwd).name.lower().replace(" ", "-")


def get_memory_dir(cwd: str) -> Path:
    encoded = cwd.replace(":", "").replace("\\", "-").replace("/", "-").strip("-")
    return HOME / ".claude" / "projects" / encoded / "memory"


def read_brief(memory_dir: Path, slug: str) -> str:
    path = memory_dir / "session_briefs" / f"{slug}.md"
    if not path.exists():
        return ""
    content = path.read_text(encoding="utf-8", errors="replace")
    # Remove frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2].strip()
    return content


def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except Exception:
        print(json.dumps({"continue": True}))
        sys.exit(0)

    cwd = data.get("cwd", "")
    if not cwd:
        print(json.dumps({"continue": True}))
        sys.exit(0)

    slug = get_project_slug(cwd)
    memory_dir = get_memory_dir(cwd)
    brief = read_brief(memory_dir, slug)

    if not brief:
        print(json.dumps({"continue": True}))
        sys.exit(0)

    context = f"## Last session context — {slug}\n\n{brief}"

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context
        }
    }))


if __name__ == "__main__":
    main()
