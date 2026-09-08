---
name: memory-save
description: Save what was learned in this session as memory notes. Run it before you close a session that produced something worth keeping.
---

You are saving what this session learned, so it comes back on its own later.

## Why this exists, and why it is not the automatic brief

Two different things get written, and the difference decides whether the memory
is worth anything.

**The automatic brief** is written by a hook at the end of every session, with no
model involved. It copies your first substantial sentence and the last thing the
assistant said. It is cheap, it always runs, and it is **heuristic** — it can be
wrong, shallow, or about the wrong part of the session.

**A curated note is written here, by you and the assistant together.** It says
what was actually learned, in a form that will make sense to someone who was not
in this conversation.

The engine knows the difference: a brief marked `curated: true` is **never
overwritten** by the automatic one. Instead a dated footer is appended saying
work happened afterwards — so a curated summary is preserved without silently
freezing.

**A memory of only automatic briefs decays into a log of first sentences.** This
command is what stops that.

---

## Step 1 — Decide what is actually worth keeping

Read back over the session and pick out only what satisfies one of these:

- **A decision, with the reason** — especially the alternatives that were
  rejected and why. Six months from now the reason is what nobody remembers.
- **A finding that cost something to get** — a measurement, a root cause, a
  behaviour that was not documented anywhere.
- **A correction** — something that was believed, then disproved. These are the
  highest-value notes and the ones most often skipped, because writing them down
  means writing down having been wrong.
- **A constraint discovered in reality** — a limit, a rate, an incompatibility.

Do **not** save: what the code already says, what the commit history already
records, or a narration of what happened. If a future reader could get it by
reading the repository, it is not memory — it is duplication that will go stale.

**If nothing meets the bar, say so and stop.** An empty save is a correct
outcome, and far better than a note nobody will ever want.

---

## Step 2 — Write each one as its own note

One idea per file, in this project's memory folder:

    ~/.claude/projects/<encoded-project-path>/memory/<name>.md

```markdown
---
name: short-kebab-case-name
description: One or two sentences saying what this is. THIS IS INDEXED — write
  the words someone would actually type when they hit this problem, not a title.
scope: project
type: concept
---

# The point, as a sentence

What was believed before, what turned out to be true, and how that was
established. Numbers where there are numbers, and where they came from.
```

Three fields decide whether the note is ever seen again:

- **`description`** is the highest-leverage line in the file. It is indexed
  alongside the body, and it is what makes the note reachable. Write it as **the
  problem, in the words of someone who has it** — not as a title. The search is
  lexical: if the note says "four" and the person types "fourth", it will not be
  found.
- **`scope: global`** makes the note travel to every project. Use it when the
  lesson does not depend on this codebase. Use `scope: project` — the default —
  when it does. Getting this wrong in the cautious direction traps a useful
  lesson in one folder.
- **The name** is what a human sees in the injected context. Make it the claim,
  not the topic.

---

## Step 3 — Update the brief, and mark it curated

Write `~/.claude/projects/<encoded>/memory/session_briefs/<slug>.md`:

```markdown
---
name: Brief — <slug>
description: Last session of project <slug>
type: project
curated: true
---

**Date:** <today>
**Project:** <name>

**What was done:** the two or three things that actually happened.
**Next step:** the first thing the next session should do — concretely enough
to start without re-reading this whole file.
**Blocker:** what is stopping progress, and who or what it is waiting on.
```

**`curated: true` is what protects it.** Without that line, the automatic hook
overwrites this at the end of the next session.

---

## Step 4 — Verify, do not assert

Do not report this as saved because you wrote files. Prove it:

1. Rebuild the index: `python ~/.claude/hooks/reindex_memory.py`
2. For each new note, ask the question someone would genuinely type about it, and
   confirm the note comes back:

   ```bash
   echo '{"prompt":"<the natural question>","cwd":"<this project>"}' \
     | python ~/.claude/hooks/prompt_memory.py
   ```

3. If it does not come back, the note is not saved in any way that matters — it
   is a file. Fix the `description` with the words from the question and try
   again.

**A note that does not return when the subject comes up is a document someone has
to remember to open**, which is the thing this whole system exists to avoid.

---

## Step 5 — Report

Three lines, no more:

- what was saved, by name
- what was deliberately not saved, and why
- what the next session should start with

If you verified reachability in step 4, say which notes you tested. If you did
not, say that instead — an unverified save is a claim, not a result.
