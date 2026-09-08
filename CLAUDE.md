# Working on this repository

Claude Code reads this file automatically when you open this folder. It exists so
you do not have to explain the project to your assistant before getting help with
it — which is, in miniature, the entire point of what is in here.

## What this is

Three parts that install together:

| folder | what it is |
|---|---|
| `engine/` | the memory. Hooks that write a session brief, index every note, and inject the relevant ones into the next prompt. |
| `method/` | six gates: `PreToolUse` hooks that **refuse** an action, plus a snapshot that saves the memory directory to git on its own. |
| `knowledge/` | 56 lessons, written as notes the engine indexes. They surface by themselves when their subject comes up. |

**No dependencies.** Python standard library only, Python 3.8+. If you are about
to add a package, that is a design change, not a detail — the whole project is
chosen against having a runtime to maintain. See "Philosophy" in `README.md`.

## Before changing anything

**Run the suite first, so you know what green looked like before you touched it:**

```bash
python engine/tests/test_memory.py             # 36 checks on the memory guards
python engine/tests/golden_recall.py           # ranking + performance gate
python engine/tests/golden_recall.py --mutate  # break it on purpose
python method/gates/tests/test_gates.py        # 39 checks on the gates + mutation
```

All four run against synthetic corpora in `engine/tests/fixtures/`. **They never
touch real notes**, and neither should anything you add — an earlier version of
this suite moved the live index aside while it ran, which broke recall for
whatever session happened to be open.

## The rule that governs the tests

**A check that has only ever passed is not evidence.** Both suites carry a
mutation mode that deliberately breaks what each check protects and fails if the
check does not notice.

If you add a check, add its mutation. If you cannot break the thing and watch the
check go red, you have not demonstrated that the check works — you have
demonstrated that it runs.

Seven real defects in this codebase were found by the tests rather than by
reading, including a gate that died the first time it tried to refuse anything,
and a backup that returned files 38 bytes larger than it stored them.

## Things that will bite you

- **Read stdin as bytes and decode UTF-8 explicitly; write stdout as UTF-8
  explicitly.** On Windows the console is cp1252 and the hook payload is UTF-8.
  Getting either wrong produces a hook that looks installed and is silently
  inert. Two shipped that way. `method/gates/gate_lib.py` documents both.
- **Never resolve the home directory literally.** Use `gl.claude_home()` /
  `memory_config`, which honour `CLAUDE_HOME`. Hardcoding it made a sandboxed
  test operate on the real memory while believing it was isolated.
- **Destructive writes are atomic** — temp file plus `os.replace`, never
  `write_text` on the target. `write_text` truncates before it knows whether it
  can encode.
- **Content containing shell or code goes through a file-writing tool, never a
  shell heredoc.** A nested heredoc reusing a delimiter deleted five scripts
  here. `knowledge/the-text-you-write-can-be-executed.md` has the details.

## Where the numbers come from

`engine/docs/MEASUREMENTS.md` records what was measured for every default —
including the semantic-search upgrade that was **built, measured and rejected**,
with the condition that would reopen it. Read it before changing a weight, a
budget or a cap: each default is holding something up, and the file says what.

## About the lessons in `knowledge/`

The lessons are real. **The stories illustrating them are reconstructed**, and
every note says so, because the originals contained operational detail belonging
to other people. Treat a figure there as showing the shape of a failure, never as
a citation.

If you add one: the `description` is the highest-leverage line in the file. It is
indexed, and the search is **lexical with no stemming** — a note saying "four" is
not found by someone typing "fourth". Write the words a person with the problem
would actually type.

## What not to do here

- Do not add a dependency without treating it as a design decision.
- Do not add a check without its mutation.
- Do not put a real credential in a fixture, even a fake-looking one — the
  `snapshot` gate will refuse to commit and you will lose time finding out why.
- Do not edit `engine/tests/fixtures/claude_home/projects/_index/` — it is
  derived and rebuilt on every run.
