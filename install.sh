#!/bin/bash
# claude-memory-hooks — install script
# Copies hooks to ~/.claude/hooks/ and registers them in settings.json

set -e

HOOKS_DIR="$HOME/.claude/hooks"
CONFIG_DIR="$HOME/.claude/memory-hooks"
SETTINGS="$HOME/.claude/settings.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing claude-memory-hooks..."

# Create directories
mkdir -p "$HOOKS_DIR"
mkdir -p "$CONFIG_DIR"

# Copy hooks
cp "$SCRIPT_DIR/hooks/auto_brief.py" "$HOOKS_DIR/"
cp "$SCRIPT_DIR/hooks/session_context.py" "$HOOKS_DIR/"
cp "$SCRIPT_DIR/hooks/prompt_memory.py" "$HOOKS_DIR/"

echo "✓ Hooks copied to $HOOKS_DIR"

# Copy skill
SKILLS_DIR="$HOME/.claude/commands"
mkdir -p "$SKILLS_DIR"
cp "$SCRIPT_DIR/skills/memory-setup/SKILL.md" "$SKILLS_DIR/memory-setup.md"

echo "✓ Skill /memory-setup installed"

# Register hooks in settings.json
if [ ! -f "$SETTINGS" ]; then
    echo '{}' > "$SETTINGS"
fi

python3 - <<'PYEOF'
import json, os, sys
from pathlib import Path

HOME = Path.home()
SETTINGS = HOME / ".claude" / "settings.json"
HOOKS_DIR = HOME / ".claude" / "hooks"

try:
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
except Exception:
    settings = {}

if "hooks" not in settings:
    settings["hooks"] = {}

hooks = settings["hooks"]

# SessionStart
if "SessionStart" not in hooks:
    hooks["SessionStart"] = []
session_cmd = f'python "{HOOKS_DIR}/session_context.py"'
if not any(h.get("command") == session_cmd for group in hooks["SessionStart"] for h in group.get("hooks", [])):
    hooks["SessionStart"].append({
        "hooks": [{"type": "command", "command": session_cmd, "timeout": 10}]
    })

# UserPromptSubmit
if "UserPromptSubmit" not in hooks:
    hooks["UserPromptSubmit"] = []
prompt_cmd = f'python "{HOOKS_DIR}/prompt_memory.py"'
if not any(h.get("command") == prompt_cmd for group in hooks["UserPromptSubmit"] for h in group.get("hooks", [])):
    hooks["UserPromptSubmit"].append({
        "hooks": [{"type": "command", "command": prompt_cmd, "timeout": 5}]
    })

# Stop
if "Stop" not in hooks:
    hooks["Stop"] = []
stop_cmd = f'python "{HOOKS_DIR}/auto_brief.py"'
if not any(h.get("command") == stop_cmd for group in hooks["Stop"] for h in group.get("hooks", [])):
    hooks["Stop"].append({
        "hooks": [{"type": "command", "command": stop_cmd, "timeout": 120}]
    })

SETTINGS.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")
print("✓ Hooks registered in settings.json")
PYEOF

echo ""
echo "Installation complete."
echo ""
echo "Next step: open Claude Code and run /memory-setup"
echo "It will ask about your projects and configure everything."
