# claude-memory-hooks

> Claude Code remembers. No server, no database, no API key, no dependencies.

[Leia em Português](README.pt-br.md) · [Where the defaults come from](docs/MEASUREMENTS.md)

---

## The problem

If you use Claude Code seriously, you have hit these walls:

1. **Claude forgets everything between sessions** — you re-explain the same context daily.
2. **Many projects, no continuity** — switching projects means starting from scratch.
3. **Work disappears when you do not save it** — close the session and the reasoning behind a decision is gone.

## What this does

Four scripts that run silently inside Claude Code:

| Script | Runs | What it does |
|---|---|---|
| `session_context.py` | session opens | Injects the last brief for this project |
| `prompt_memory.py` | you type a prompt | Ranks every note you have and injects the relevant ones |
| `auto_brief.py` | session closes | Writes the brief from the transcript |
| `reindex_memory.py` | session opens and closes | Keeps the search index current |

Memory is stored as plain Markdown you can read, edit, move or delete. Removing
the tool does not remove the memory.

**No LLM calls. No API key. Nothing running in the background. Python standard
library only.**

---

## How it feels

**Before**

> You: "So, continuing from yesterday, we were on the payment webhook where the retry—"
> Claude: "I don't have context from previous sessions..."

**After**

> *(session opens)*
> Claude already knows: the project, the last task, the next step, what is blocked.
> You just continue.

And mid-conversation, when you mention something you worked on weeks ago in a
different project, the note comes back on its own — you did not have to remember
that it existed.

---

## Install

**Requirements:** Python 3.8+ and Claude Code. That is the whole list.

```bash
git clone https://github.com/oliveirarenanfelipe/claude-memory-hooks
cd claude-memory-hooks
bash install.sh
```

Restart Claude Code. It works immediately with no configuration.

To tune it, run `/memory-setup` — a short guided conversation that writes the
config for you. To remove everything: `bash uninstall.sh` (your notes stay).

The installer is idempotent: run it again to upgrade, and it will not register
anything twice. It backs up `settings.json` before touching it.

---

## How it actually works

Claude Code hooks can return `hookSpecificOutput.additionalContext`. **Any text
you put there is injected into the model's context.** That is the entire
mechanism — everything else in this repository is about deciding *which* text.

Deciding well is the hard part:

- **Ranked retrieval, not keyword matching.** BM25 over every note in every
  project, with an inverted index so a search costs about a millisecond.
- **It knows where you are standing.** A note from the project you have open
  outranks one from a neighbour — as a multiplier, never a filter, so the
  neighbour's note still wins when it is genuinely the answer.
- **Long notes are sliced by heading, not truncated.** Something written near the
  end of a 20,000-character note is still findable.
- **Results are deduplicated by file**, so one long document cannot take all five
  slots and push out the other four answers.
- **A hand-written brief is never overwritten.** Mark it `curated: true` and the
  automatic one steps aside, leaving a dated footer saying work happened after it.
- **When no memory is injected, the log says why.** "Too slow" and "found
  nothing" need opposite fixes and must never look the same.

Every number behind those choices — the budget, the weights, the slice size — was
measured on a real corpus. They are written down in
[docs/MEASUREMENTS.md](docs/MEASUREMENTS.md), along with what was tried and
rejected.

---

## Configuration

Everything is optional. Copy `memory-hooks/config.example.json` to
`~/.claude/memory-hooks/config.json` and keep only what you change.

```json
{
  "language": "en",
  "project_roots": ["/Users/me/code"],
  "layers": [
    { "name": "handbook", "path": "/Users/me/notes/handbook",
      "mode": "flat", "scope": "global" }
  ]
}
```

- **`project_roots`** — where your projects live. Only affects how project names
  are displayed: with it, `app`; without it, `users-me-code-app`. Both work.
- **`layers`** — note folders outside `~/.claude/projects/`: a handbook, an
  Obsidian vault, a folder of standards. `scope: "global"` makes a layer relevant
  in every project. Prefer a `folders` whitelist over `mode: "recursive"` — a
  recursive sweep over a folder nobody curated will pull in whatever is sitting
  there.
- **`weights`, `budget_ms`, `note_cap`** — the ranking and performance knobs.
  Read [docs/MEASUREMENTS.md](docs/MEASUREMENTS.md) before changing one; each
  default is holding something up.

A malformed config falls back to the defaults instead of breaking your session.

---

## Tests, and a gate that can fail

```bash
python tests/test_memory.py             # 36 checks on the guards
python tests/golden_recall.py           # ranking + performance gate
python tests/golden_recall.py --mutate  # break it on purpose; the gate must fail
```

No pytest, no dependencies, and they run against a synthetic corpus in
`tests/fixtures/` — never your own notes.

`golden_recall.py` names *which* note must come back and *how high*. A test that
only asserts "some results came back" stays green while the ranking is destroyed.

`--mutate` is the part worth copying into your own projects. It deliberately
breaks the thing each case protects — makes neighbours outrank the open project,
removes the extra layers, switches slicing off — and **fails if the gate does not
notice**. A gate that has only ever passed is not evidence; it will stay green
through a real regression too.

CI runs all three on Linux, macOS and Windows, on Python 3.8 and 3.12.

---

## Where your memory lives

```
~/.claude/
  projects/<encoded-project-path>/memory/
      project_*.md              your notes
      session_briefs/<slug>.md  the automatic brief
  memory-hooks/config.json      your config
  hooks/recall.log              why each prompt got the memory it got
```

The index (`projects/_index/`) is derived. Delete it any time; the next session
rebuilds it from the Markdown.

---

## Philosophy

This started by studying [claude-mem](https://github.com/thedotmack/claude-mem),
which runs a persistent local server, SQLite and ChromaDB for semantic search.
It is a powerful piece of work.

This does the same core job with Python scripts and Markdown files. Nothing to
keep running, nothing to break, nothing to pay for, and no service that can
disappear and take your memory with it.

The trade is real and worth stating plainly: **lexical search, not semantic.** If
you ask about "authentication" and your note says "login", BM25 will not connect
them — a vector store would. In exchange you get results you can explain, an
index that rebuilds in seconds, zero infrastructure, and notes that stay
yours in a format that will still open in ten years.

---

## License

MIT — do whatever you want with it.
