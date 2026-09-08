#!/usr/bin/env bash
# claude-memory-hooks — installer
#
#   bash install.sh              the memory only (default)
#   bash install.sh --full       the memory plus the method: gates and snapshots
#   bash install.sh --full --yes assume yes to the snapshot repository question
#
# Idempotent: run it again to upgrade; nothing is ever registered twice.
# Nothing is downloaded, nothing is compiled, there are no dependencies.
#
# Override the target with CLAUDE_HOME=/some/path bash install.sh

set -euo pipefail

LEVEL="engine"
ASSUME_YES="no"
for arg in "$@"; do
  case "$arg" in
    --full) LEVEL="full" ;;
    --engine) LEVEL="engine" ;;
    --yes|-y) ASSUME_YES="yes" ;;
    -h|--help)
      echo "usage: bash install.sh [--full] [--yes]"
      echo "  (default)  the memory: remembers across sessions, recalls what matters"
      echo "  --full     also the method: gates that refuse, plus automatic snapshots"
      echo "  --yes      do not ask about creating the snapshot repository"
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
           project_boundary.py context_budget.py snapshot.py redact_secrets.py; do
    cp "$SRC/method/gates/$f" "$GATES_DIR/$f"
  done
  echo "  method: 7 gate scripts copied"
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
cp "$SRC/engine/memory-save.md" "$COMMANDS_DIR/memory-save.md"
echo "  /memory-setup and /memory-save installed"

CLAUDE_HOME="$CLAUDE_DIR" "$PY" "$SRC/tools/register_hooks.py" --install --level "$LEVEL"

# The snapshot needs a repository to save into. Left as a line of output, people
# do not do it — and then a protection is installed that protects nothing. So it
# is offered, with the ignore list already in place. It is declined by default:
# creating a repository inside someone's home directory is not something to do
# without being asked.
if [ "$LEVEL" = "full" ] && [ ! -d "$CLAUDE_DIR/.git" ]; then
  echo
  echo "  The automatic snapshot saves your memory into a git repository, so a"
  echo "  deleted file is one command away instead of gone. There is no"
  echo "  repository in $CLAUDE_DIR yet, so right now it does nothing."
  echo
  echo "  Set it up? It stays entirely local — no remote is added, nothing is"
  echo "  uploaded. An ignore list is installed first, which keeps out the"
  echo "  transcripts, the caches and anything credential-shaped."

  ANSWER="n"
  if [ "$ASSUME_YES" = "yes" ]; then
    ANSWER="y"
  elif [ -t 0 ]; then
    printf "  [y/N] "
    read -r ANSWER || ANSWER="n"
  else
    echo "  (not a terminal — skipping the question; re-run with --yes to accept)"
  fi

  case "$ANSWER" in
    [yY]*)
      cp "$SRC/method/memory-dir.gitignore" "$CLAUDE_DIR/.gitignore"
      cp "$SRC/method/memory-dir.gitattributes" "$CLAUDE_DIR/.gitattributes"
      git -C "$CLAUDE_DIR" init -q
      git -C "$CLAUDE_DIR" config core.autocrlf false
      echo "  repository created, with the ignore list already in place."
      echo
      echo "  Look at what would be saved BEFORE the first snapshot runs:"
      echo "      git -C \"$CLAUDE_DIR\" status --short | head -40"
      echo "  The snapshot refuses to commit anything credential-shaped, but the"
      echo "  first review is worth doing with your own eyes."
      ;;
    *)
      echo "  skipped. The snapshot stays inert until you run:"
      echo "      cp \"$SRC/method/memory-dir.gitignore\" \"$CLAUDE_DIR/.gitignore\""
      echo "      cd \"$CLAUDE_DIR\" && git init"
      ;;
  esac
fi

echo
echo "Done. Restart Claude Code."
echo
echo "  /memory-setup   tune it for your projects (optional — defaults work)"
echo "  /memory-save    save what a session learned, as curated notes"
echo
echo "The first automatic brief is written when you close a session with at"
echo "least two substantial messages in it."
echo
echo "Check the install:  CLAUDE_HOME=\"$CLAUDE_DIR\" $PY $SRC/tools/register_hooks.py --status"
echo "Build the index:    $PY $HOOKS_DIR/reindex_memory.py"
echo "Remove everything:  bash $SRC/uninstall.sh"
