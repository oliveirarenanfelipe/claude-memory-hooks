# The method

The engine remembers. This half is about how the work gets done — and it is
deliberately not a document of advice.

## Why this is code and not a style guide

Every rule here existed first as a sentence in a document. Every one of them was
violated anyway, by the person who wrote it, with the document loaded.

The clearest case is the one that produced `destructive_bash.py`. A note written
nineteen days earlier said, in those exact words, *"never through a shell
heredoc"*. It was indexed, it was recallable, and it was written after the same
class of mistake had already happened twice. The mistake happened a third time
and deleted five scripts.

So the rule of this folder is narrow: **a practice that matters is a gate, or it
is a wish.** If you cannot state the moment it fires and what it refuses, it does
not belong here — it belongs in prose, where you already know it will not hold.

## What a gate is

A Claude Code `PreToolUse` hook that can return `deny`. It sees the action about
to happen — the file about to be written, the command about to run — and can stop
it, with a message explaining why and what to do instead.

The trigger is the ACTION, never a word in the conversation. That distinction is
the whole reason gates work where checklists fail: a checklist fires when someone
remembers to classify the situation, and the moment you are about to make the
mistake is precisely the moment you have not classified it that way.

## The seven

| file | fires when | refuses |
|---|---|---|
| `no_orphan_files.py` | a new code file is about to be created | the first attempt, asking who will call it |
| `destructive_bash.py` | a shell command is about to run | deletes and overwrites inside protected paths, and nested heredocs |
| `project_boundary.py` | a file is about to be written | a write into a project other than the open one |
| `context_budget.py` | a watched instruction file is edited | an edit that pushes it past its size budget |
| `redact_secrets.py` | a tool returns a result | nothing - it rewrites credential-shaped values out of the result before it reaches the conversation |
| `question_is_analysis.py` | you write or run something | the FIRST action of a turn whose message was a question, not an instruction |
| `snapshot.py` | a turn ends | nothing — it saves the memory directory to git, and refuses to save secrets |

## Two kinds of refusal, and the difference matters

**Refusals that make something visible** — `no_orphan_files`, `project_boundary`,
`context_budget` — interrupt ONCE. Answer, repeat the action, and it goes through.
The cost is one sentence saying why, which is exactly the value: the reasoning
happens in the open instead of silently.

**Refusals that protect something irreversible** — `destructive_bash` — never
yield to repetition. They require an explicit written marker (`# GATE-OK: reason`)
in the command itself. A guard on a destructive action that gives up on the second
attempt is decoration, and the marker cannot appear by accident, which is the
whole failure mode being guarded against.

## The half of the test suite that keeps these installed

`tests/test_gates.py` has a section called MUST ALLOW, and it is not politeness.
A gate that blocks legitimate work becomes a tax, and a tax gets uninstalled
within a week — after which it protects nothing at all. Every gate here has to
prove it stays out of the way of the ordinary case:

```bash
python method/gates/tests/test_gates.py
```

56 checks, and five mutations that disarm each detector and require the
behaviour to change. A gate that has only ever passed is not evidence.

## Install

```bash
bash install.sh --full
```

Without `--full` you get the engine only. The gates are opt-in because they
change how your sessions behave — they will refuse things, and that should be a
decision rather than a surprise.

## Configuring them

Everything is in `~/.claude/memory-hooks/config.json`, under `gates`. With no
configuration, `no_orphan_files` and `destructive_bash` work on sensible
defaults; `project_boundary` needs to know where your projects live, and
`context_budget` does nothing at all until you name the file it should watch —
guessing which document is sacred to you would be worse than silence.

See `engine/config/config.example.json`.

## Before turning on the snapshot

`snapshot.py` commits your memory directory to git. That directory can hold
credentials — the setup this came from had two access tokens and an API key
sitting in plain text inside notes, for months, and found them only when
something finally looked.

The snapshot refuses to commit anything matching a credential pattern and writes
which file stopped it. Treat that refusal as a finding, not an obstacle: a secret
in plain text is a problem with or without git, and a secret that reaches git
history cannot be taken back out.

## Adding your own

Read `gate_lib.py` first. It carries the four rules every gate here follows —
including the two encoding rules, each of which has already produced a gate that
looked installed and was silently inert, and one of which was caught only because
a test tried to make the gate refuse and it died instead.
