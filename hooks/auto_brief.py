#!/usr/bin/env python3
"""
auto_brief.py — Stop hook
Automatically generates a session brief at the end of every Claude Code session.
Reads the session transcript, extracts what was done, saves to the project memory directory.

No LLM calls. No API key needed. No external dependencies.
"""
import json
import sys
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

HOME = Path.home()


def get_project_slug(cwd: str) -> str:
    """Detect project name from git remote or directory name."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=cwd, capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            remote = result.stdout.strip()
            # Extract repo name from URL (github.com/user/repo or git@github.com:user/repo)
            name = remote.rstrip("/").split("/")[-1].replace(".git", "")
            if name:
                return name.lower()
    except Exception:
        pass
    # Fallback: directory name
    return Path(cwd).name.lower().replace(" ", "-")


def get_memory_dir(cwd: str) -> Path:
    """Get the Claude Code memory directory for this project."""
    # Claude Code encodes cwd as directory name under ~/.claude/projects/
    encoded = cwd.replace(":", "").replace("\\", "-").replace("/", "-").strip("-")
    return HOME / ".claude" / "projects" / encoded / "memory"


def read_transcript(path: str) -> list:
    messages = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    role = d.get("message", {}).get("role", "")
                    if role not in ("user", "assistant"):
                        continue
                    content = d["message"].get("content", "")
                    text = ""
                    if isinstance(content, list):
                        for c in content:
                            if isinstance(c, dict) and c.get("type") == "text":
                                text = c.get("text", "")
                                break
                    elif isinstance(content, str):
                        text = content
                    text = text.strip()
                    if text and len(text) > 15 and not text.startswith("<tool_result"):
                        messages.append({"role": role, "text": text})
                except Exception:
                    pass
    except Exception:
        pass
    return messages


def first_sentence(text: str, max_chars: int = 200) -> str:
    text = text.replace("\n", " ").strip()
    for sep in [". ", "! ", "? "]:
        idx = text.find(sep)
        if 0 < idx < max_chars:
            return text[:idx + 1].strip()
    return text[:max_chars].strip()


def extract_files(messages: list) -> list:
    pattern = re.compile(r'[`\s]([A-Za-z0-9_/\\.-]+\.[a-z]{2,5})\b')
    files = set()
    for m in messages:
        for match in pattern.findall(m["text"]):
            if any(match.endswith(ext) for ext in ['.py', '.js', '.ts', '.json', '.md', '.sh', '.yml', '.yaml', '.html', '.css']):
                files.add(match)
    return list(files)[:6]


def extract_what_done(messages: list) -> str:
    user_msgs = [m for m in messages if m["role"] == "user"]
    assistant_msgs = [m for m in messages if m["role"] == "assistant"]
    lines = []
    for m in user_msgs:
        if len(m["text"]) > 30:
            lines.append(first_sentence(m["text"], 200))
            break
    if assistant_msgs:
        last = assistant_msgs[-1]["text"]
        paragraphs = [p.strip() for p in last.split("\n\n") if len(p.strip()) > 30]
        if paragraphs:
            lines.append(paragraphs[0][:300].replace("\n", " "))
    return " — ".join(lines)[:500] if lines else "Work session."


def extract_next_step(messages: list) -> str:
    keywords = ["next step", "próximo passo", "to do", "a seguir", "falta", "pendente"]
    assistant_msgs = [m for m in messages if m["role"] == "assistant"]
    for m in reversed(assistant_msgs[-4:]):
        text_lower = m["text"].lower()
        for kw in keywords:
            if kw in text_lower:
                for sentence in m["text"].split("."):
                    if kw in sentence.lower() and len(sentence.strip()) > 15:
                        return sentence.strip()[:250]
    user_msgs = [m for m in messages if m["role"] == "user"]
    if user_msgs:
        return f"Continue from: {first_sentence(user_msgs[-1]['text'], 150)}"
    return "Review session and continue."


def detect_blocker(messages: list) -> str:
    keywords = ["blocked", "bloqueado", "waiting", "aguardando", "pending", "pendente", "not tested", "não testado"]
    for m in reversed(messages[-6:]):
        text_lower = m["text"].lower()
        for kw in keywords:
            if kw in text_lower:
                for sentence in m["text"].split("."):
                    if kw in sentence.lower() and len(sentence.strip()) > 15:
                        return sentence.strip()[:200]
    return "None."


def save_brief(memory_dir: Path, slug: str, content: str, session_id: str):
    briefs_dir = memory_dir / "session_briefs"
    briefs_dir.mkdir(parents=True, exist_ok=True)
    path = briefs_dir / f"{slug}.md"
    frontmatter = f"---\nproject: {slug}\nsession: {session_id}\ndate: {datetime.now().strftime('%Y-%m-%d')}\n---\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(frontmatter + content)


def notify(message: str):
    """Print a subtle touch point notification."""
    print(json.dumps({
        "continue": True,
        "suppressOutput": False,
        "systemMessage": message
    }))


def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except Exception:
        sys.exit(0)

    transcript_path = data.get("transcript_path") or data.get("transcriptPath", "")
    cwd = data.get("cwd", "")
    session_id = data.get("session_id") or data.get("sessionId", "unknown")

    if not transcript_path or not os.path.exists(transcript_path):
        print(json.dumps({"continue": True, "suppressOutput": True}))
        sys.exit(0)

    messages = read_transcript(transcript_path)
    user_msgs = [m for m in messages if m["role"] == "user"]

    if len(user_msgs) < 2:
        print(json.dumps({"continue": True, "suppressOutput": True}))
        sys.exit(0)

    slug = get_project_slug(cwd)
    memory_dir = get_memory_dir(cwd)
    files = extract_files(messages)
    files_line = f"\n**Files touched:** {', '.join(f'`{f}`' for f in files)}" if files else ""

    brief = (
        f"**Date:** {datetime.now().strftime('%Y-%m-%d')}\n"
        f"**Project:** {slug}\n\n"
        f"**What was done:** {extract_what_done(messages)}\n"
        f"{files_line}\n\n"
        f"**Next step:** {extract_next_step(messages)}\n\n"
        f"**Blocker:** {detect_blocker(messages)}"
    )

    save_brief(memory_dir, slug, brief, session_id)
    notify(f"📝 Brief saved — {slug}")


if __name__ == "__main__":
    main()
