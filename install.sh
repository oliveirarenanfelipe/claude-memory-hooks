#!/usr/bin/env bash
# claude-memory-hooks — installer
#
#   bash install.sh              the memory only (default)
#   bash install.sh --full       the memory plus the method: gates and snapshots
#
# Idempotent: run it again to upgrade; nothing is ever registered twice.
# Nothing is downloaded, nothing is compiled, there are no dependencies.
#
# Override the target with CLAUDE_HOME=/some/path bash install.sh

set -euo pipefail

LEVEL="engine"
for arg in "$@"; do
  case "$arg" in
    --full) LEVEL="full" ;;
    --engine) LEVEL="engine" ;;
    -h|--help)
      echo "usage: bash install.sh [--full]"
      echo "  (default)  the memory: remembers across sessions, recalls what matters"
      echo "  --full     also the method: gates that refuse, plus automatic snapshots"
      exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 1 ;;
  esac
done

CLAUDE_DIR="${CLAUDE_HOME:-$HOME/.claude}"
HOOKS_DIR="$CLAUDE_DIR/hooks"
GATES_DIR="$CLAUDE_DIR/gates"
CONFIG_DIR="$CLAUDE_DIR/memory-hooks"
COMMANDS_DIR="$CLAUDE_DIR/commands"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Windows (Git Bash) ships `python`; most other places ship `python3`.
PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
  echo "Python 3.8+ is required and was not found on PATH." >&2
  exit 1
fi

echo "Installing claude-memory-hooks into $CLAUDE_DIR  (level: $LEVEL)"

mkdir -p "$HOOKS_DIR" "$CONFIG_DIR" "$COMMANDS_DIR"

for f in memory_config.py memory_lib.py session_context.py prompt_memory.py \
         auto_brief.py reindex_memory.py; do
  cp "$SRC/engine/hooks/$f" "$HOOKS_DIR/$f"
done
echo "  engine: 6 scripts copied"

if [ "$LEVEL" = "full" ]; then
  mkdir -p "$GATES_DIR"
  for f in gate_lib.py no_orphan_files.py destructive_bash.py \
           project_boundary.py context_budget.py snapshot.py; do
    cp "$SRC/method/gates/$f" "$GATES_DIR/$f"
  done
  echo "  method: 6 gate scripts copied"
fi

# The example is always refreshed; your own config.json is never overwritten,
# because it is the one file in here that belongs to you.
cp "$SRC/engine/config/config.example.json" "$CONFIG_DIR/config.example.json"
if [ -f "$CONFIG_DIR/config.json" ]; then
  echo "  existing config.json left untouched"
else
  echo "  no config.json yet — the defaults work as they are"
fi

cp "$SRC/engine/memory-setup.md" "$COMMANDS_DIR/memory-setup.md"
echo "  /memory-setup installed"

CLAUDE_HOME="$CLAUDE_DIR" "$PY" "$SRC/tools/register_hooks.py" --install --level "$LEVEL"

if [ "$LEVEL" = "full" ] && [ ! -d "$CLAUDE_DIR/.git" ]; then
  echo
  echo "  NOTE: the automatic snapshot needs a git repository to save into."
  echo "  It does nothing until you create one:"
  echo "      cd \"$CLAUDE_DIR\" && git init"
  echo "  Read method/README.md first — that directory can hold secrets, and the"
  echo "  method folder ships the ignore list that keeps them out."
fi

echo
echo "Done. Restart Claude Code, then either run /memory-setup or just start"
echo "working — the first session brief is written when you close a session."
echo
echo "Check the install:  CLAUDE_HOME=\"$CLAUDE_DIR\" $PY $SRC/tools/register_hooks.py --status"
echo "Build the index:    $PY $HOOKS_DIR/reindex_memory.py"
echo "Remove everything:  bash $SRC/uninstall.sh"
