#!/usr/bin/env bash
# claude-memory-hooks — installer
#
# Copies the hooks into ~/.claude/hooks/ and registers them in settings.json.
# Idempotent: running it again upgrades the files and never duplicates a hook.
# Nothing is downloaded, nothing is compiled, there are no dependencies.
#
# Override the target with CLAUDE_HOME=/some/path bash install.sh

set -euo pipefail

CLAUDE_DIR="${CLAUDE_HOME:-$HOME/.claude}"
HOOKS_DIR="$CLAUDE_DIR/hooks"
CONFIG_DIR="$CLAUDE_DIR/memory-hooks"
COMMANDS_DIR="$CLAUDE_DIR/commands"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Windows (Git Bash) ships `python`; most other places ship `python3`.
PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
  echo "Python 3.8+ is required and was not found on PATH." >&2
  exit 1
fi

echo "Installing claude-memory-hooks into $CLAUDE_DIR"

mkdir -p "$HOOKS_DIR" "$CONFIG_DIR" "$COMMANDS_DIR"

for f in memory_config.py memory_lib.py session_context.py prompt_memory.py \
         auto_brief.py reindex_memory.py; do
  cp "$SRC/hooks/$f" "$HOOKS_DIR/$f"
done
echo "  6 hook scripts copied"

# The example is always refreshed; your own config.json is never overwritten,
# because it is the one file in here that belongs to you.
cp "$SRC/memory-hooks/config.example.json" "$CONFIG_DIR/config.example.json"
if [ -f "$CONFIG_DIR/config.json" ]; then
  echo "  existing config.json left untouched"
else
  echo "  no config.json yet — the defaults work as they are"
  echo "  example placed at $CONFIG_DIR/config.example.json"
fi

cp "$SRC/skills/memory-setup/SKILL.md" "$COMMANDS_DIR/memory-setup.md"
echo "  /memory-setup installed"

CLAUDE_HOME="$CLAUDE_DIR" "$PY" "$SRC/tools/register_hooks.py" --install

echo
echo "Done. Restart Claude Code, then either run /memory-setup or just start"
echo "working — the first session brief is written when you close a session."
echo
echo "Check the install:  CLAUDE_HOME=\"$CLAUDE_DIR\" $PY $SRC/tools/register_hooks.py --status"
echo "Build the index:    $PY $HOOKS_DIR/reindex_memory.py"
echo "Remove everything:  bash $SRC/uninstall.sh"
