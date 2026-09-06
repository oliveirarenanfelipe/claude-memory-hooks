---
name: memory-setup
description: Configure claude-memory-hooks for your projects. Run this once after installing, or any time your setup changes.
---

You are configuring claude-memory-hooks for this user.

Two things to hold on to while you do it:

1. **The hooks already work with no configuration.** Everything below is tuning,
   not setup. Never leave the user with the impression that they must answer all
   of this before memory works — they do not.
2. **Read the current config before asking anything.** If
   `~/.claude/memory-hooks/config.json` exists, open it and say what is already
   there. Asking someone to re-answer questions they answered last month is the
   fastest way to make a tool feel disposable.

---

## Step 0 — look before you ask

- Read `~/.claude/memory-hooks/config.json` if it exists.
- List the folders under `~/.claude/projects/` — those are the projects Claude
  Code already knows about, and the names are encoded paths (`C--Users-me-code-app`
  means `C:\Users\me\code\app`).
- Run `python ~/.claude/hooks/reindex_memory.py` and report how many notes were
  found. If it says zero, the interesting question is not about keywords: it is
  that this user has no notes yet, and you should tell them the first brief
  appears when they close their next session.

Summarise what you found in two or three lines, then ask only what is missing.

---

## Step 1 — the one question that pays for itself

> "Do all your projects live under one folder? If so, paste that folder's path."

This becomes `project_roots`. It is worth asking first because it is the only
setting that changes what the user *sees*: with it, a project is filed under
`app`; without it, under `c-users-me-code-app`. Both work and both are stable —
one is just readable.

Accept more than one root. Accept "no" and move on.

---

## Step 2 — language

> "What language do you write your notes in?"

Sets `language` (`"en"`, `"pt"`, `"es"`, or a list like `["en", "pt"]` if they
mix). It controls two things: which short words are ignored when searching, and
the wording the automatic brief looks for when it hunts for a decision, a next
step or a blocker.

If they mix languages, use the list. There is no cost to including both.

---

## Step 3 — notes that live outside a project

> "Do you keep notes anywhere else — a handbook, an Obsidian vault, a folder of
> standards — that you would want Claude to find while working on any project?"

Each one becomes an entry in `layers`:

```json
{
  "name": "handbook",
  "path": "/absolute/path/to/folder",
  "mode": "flat",
  "scope": "global"
}
```

- `mode`: `"flat"` reads only the top level, `"recursive"` reads everything
  below. **Default to `"flat"`.**
- `folders`: a whitelist of subfolders, read one level deep each. Prefer this
  over `"recursive"` whenever the folder has anything in it that is not a note —
  drafts, downloads, exports, anything with credentials in it. A recursive sweep
  over a folder nobody curated puts junk into the search results and, worse, can
  put private material into the model's context. **Ask what else is in the
  folder before choosing recursive.**
- `scope`: `"global"` if the notes are relevant in every project (standards, a
  handbook); `"project"` if they are reference material that should not outrank
  the project's own notes.

---

## Step 4 — keyword fallback (optional, and usually skippable)

The ranked search normally finds the right note on its own. The keyword map only
runs when the search returns nothing, so treat it as a safety net for a handful
of terms the user knows they use constantly.

Only ask if they want one:

```json
"keywords": [
  { "match": ["billing", "stripe"], "files": ["project_billing.md"] }
]
```

`files` are names inside that project's own `memory/` folder.

---

## Step 5 — write it, then prove it

Write `~/.claude/memory-hooks/config.json`. Include only the keys you actually
gathered — every other default is already correct, and a config file full of
restated defaults is a file nobody dares to edit later.

Then **verify, do not assert**:

1. `python ~/.claude/hooks/reindex_memory.py` — report the note count.
2. Ask the user for a question they would genuinely type about one of their
   projects, and show them what the memory hook returns for it.
3. If it returns nothing useful, say so plainly and check `hooks/recall.log`:
   the last line names the reason. `nohit` means the notes do not contain the
   words they typed — a coverage problem, not a configuration one.

Close with where their memory lives — `~/.claude/projects/*/memory/`, plain
Markdown they can read, edit or delete — and that `bash uninstall.sh` removes the
tool without touching any of it.
