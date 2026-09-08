# claude-memory-hooks

> Claude Code remembers, and works the way you decided it should.
> No server, no database, no API key, no dependencies.

[![tests](https://github.com/oliveirarenanfelipe/claude-memory-hooks/actions/workflows/test.yml/badge.svg)](https://github.com/oliveirarenanfelipe/claude-memory-hooks/actions/workflows/test.yml)
[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![dependencies](https://img.shields.io/badge/dependencies-none-brightgreen.svg)](#)

[Leia em Português](README.pt-br.md)

---

## Three parts, one install

| | what it is | state |
|---|---|---|
| **[`engine/`](engine/)** | the memory: remembers across sessions, and recalls what is relevant to what you just typed | ready |
| **[`method/`](method/)** | how the work gets done — as gates that **refuse**, not as advice | ready |
| **[`knowledge/`](knowledge/)** | 56 lessons that survive the project they came from, shipped as notes the engine indexes | ready |

You can take just the first. The three together are the point: a memory with
nothing worth remembering is an empty filing cabinet, and a method nobody
enforces is a wish.

---

## The problem

If you use Claude Code seriously, you have hit these:

1. **It forgets everything between sessions** — you re-explain the same context daily.
2. **Many projects, no continuity** — switching projects means starting from scratch.
3. **Work disappears when you do not save it** — close the session and the reasoning behind a decision is gone.
4. **The rules you wrote get ignored** — including by you, with the document loaded.

The first three are what `engine/` is for. The fourth one is the interesting one,
and it is what `method/` is for.

---

## Install

**Requirements:** Python 3.8+ and Claude Code. That is the whole list.

```bash
git clone https://github.com/oliveirarenanfelipe/claude-memory-hooks
cd claude-memory-hooks

bash install.sh           # the memory
bash install.sh --full    # the memory plus the method
```

Restart Claude Code. It works immediately with no configuration.

`--full` is opt-in on purpose: the gates will **refuse** things. That should be a
decision, not a surprise.

Run `/memory-setup` to tune it, or `bash uninstall.sh` to remove everything —
your notes stay either way. The installer is idempotent and backs up
`settings.json` before touching it.

---

## How the memory works

Claude Code hooks can return `hookSpecificOutput.additionalContext`. **Any text
you put there is injected into the model's context.** That is the entire
mechanism — the rest is deciding *which* text.

- **Ranked retrieval, not keyword matching.** BM25 over every note in every
  project, with an inverted index, so a search costs about a millisecond.
- **It knows where you are standing.** A note from the project you have open
  outranks a neighbour's — as a multiplier, never a filter, so the neighbour's
  note still wins when it genuinely is the answer.
- **Long notes are sliced by heading, not truncated.** Something written near the
  end of a 20,000-character note is still findable.
- **Results are deduplicated by file**, so one long document cannot take all five
  slots and push out the other four answers.
- **A hand-written brief is never overwritten.** Mark it `curated: true` and the
  automatic one steps aside, leaving a dated footer saying work happened after it.
- **When no memory is injected, the log says why.** "Too slow" and "found nothing"
  need opposite fixes and must never look the same.

Every number behind those choices was measured. They are written down in
[`engine/docs/MEASUREMENTS.md`](engine/docs/MEASUREMENTS.md), along with what was
tried and rejected.

---

## Why the method is code

Every rule in `method/` existed first as a sentence in a document, and every one
of them was violated anyway — by the person who wrote it, with the document
loaded.

The clearest case: a note written nineteen days earlier said, in those exact
words, *"never through a shell heredoc"*. It was indexed and recallable. The
mistake happened anyway and deleted five scripts and five hook registrations.

So the rule is narrow: **a practice that matters is a gate, or it is a wish.**

Six of them ship: refuse a new file with nothing calling it; refuse a
destructive shell command; refuse a write into someone else's project; refuse an
edit that bloats an always-loaded instruction file; redact credential-shaped
values out of every tool result before they reach the conversation; and save the
memory directory to git on its own, refusing to save secrets.

The redaction one exists because a third-party tool returned an access token
inside a *successful* response, and it ended up in the transcript **15 times**
before anyone noticed. Filtering that one tool was the wrong fix: it would have
kept leaking the same way from somewhere else.

Details in [`method/README.md`](method/README.md).

---

## Tests, and checks that can fail

```bash
make            # all of it
python engine/tests/test_memory.py             # 36 checks on the memory guards
python engine/tests/golden_recall.py           # ranking + performance gate
python engine/tests/golden_recall.py --mutate  # break it on purpose
python method/gates/tests/test_gates.py        # 36 checks on the gates + mutation
```

No pytest, no dependencies, and they run against synthetic corpora — never your
own notes.

The part worth copying into your own projects is `--mutate`. It deliberately
breaks the thing each check protects — makes neighbours outrank the open project,
removes a layer, switches slicing off, empties the secret detector — and **fails
if the checks do not notice**. A check that has only ever passed is not evidence;
it will stay green through a real regression too.

Both suites caught real defects in this codebase during development, including a
gate that died the first time it tried to refuse anything, and a backup that
returned files 38 bytes larger than it stored them.

CI runs everything on Linux, macOS and Windows, on Python 3.8 and 3.12.

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

Plain Markdown you can read, edit, move or delete. Removing the tool does not
remove the memory.

---

## Philosophy

This started by studying [claude-mem](https://github.com/thedotmack/claude-mem),
which runs a persistent local server, SQLite and ChromaDB for semantic search.
It is a powerful piece of work.

This does the same core job with Python scripts and Markdown files. Nothing to
keep running, nothing to break, nothing to pay for, and no service that can
disappear and take your memory with it.

The trade is real and worth stating plainly: **lexical search, not semantic.** Ask
about "authentication" when your note says "login" and BM25 will not connect them;
a vector store would. In exchange you get results you can explain, an index that
rebuilds in seconds, zero infrastructure, and notes that stay yours in a format
that will still open in ten years.

---

## License

MIT — see [LICENSE](LICENSE). Do whatever you want with it.

Also here: [CHANGELOG](CHANGELOG.md) · [SECURITY](SECURITY.md) ·
[CLAUDE.md](CLAUDE.md), which gives your assistant the context for this
repository the moment you open it — the same thing the project does for your own
work.
