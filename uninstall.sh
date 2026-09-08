#!/usr/bin/env bash
# claude-memory-hooks — uninstaller
#
# Removes the hook scripts and unregisters them from settings.json.
#
# Your notes and briefs are NEVER touched. They are plain Markdown under
# ~/.claude/projects/*/memory/ and they stay exactly where they are — the whole
# point of storing memory as files you own is that removing the tool does not
# remove the memory.
#
# Override the target with CLAUDE_HOME=/some/path bash uninstall.sh

set -euo pipefail

CLAUDE_DIR="${CLAUDE_HOME:-$HOME/.claude}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
  echo "Python was not found on PATH." >&2
  exit 1
fi

echo "Removing claude-memory-hooks from $CLAUDE_DIR"

CLAUDE_HOME="$CLAUDE_DIR" "$PY" "$SRC/tools/register_hooks.py" --uninstall

for f in memory_config.py memory_lib.py session_context.py prompt_memory.py \
         auto_brief.py reindex_memory.py; do
  rm -f "$CLAUDE_DIR/hooks/$f"
done
rm -f "$CLAUDE_DIR/commands/memory-setup.md"
rm -f "$CLAUDE_DIR/commands/memory-save.md"

# Derived files only: the index and the recall log are rebuilt from the notes,
# so deleting them loses nothing that cannot be regenerated.
rm -f "$CLAUDE_DIR/projects/_index/memory_cache.json" \
      "$CLAUDE_DIR/projects/_index/memory_index.pkl" \
      "$CLAUDE_DIR/hooks/recall.log" \
      "$CLAUDE_DIR/hooks/recall.log.1"
rm -rf "$CLAUDE_DIR/hooks/__pycache__"

echo "  scripts and derived files removed"
echo
echo "Your notes, session briefs and config.json are still there:"
echo "  $CLAUDE_DIR/projects/*/memory/"
echo "  $CLAUDE_DIR/memory-hooks/config.json"
