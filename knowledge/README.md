# The knowledge

**56 lessons that survive the project they were learned in.**

They are plain notes with frontmatter, so the engine indexes them like any other
memory. Once installed, they come back **on their own** when the subject comes up
in a conversation, in any project. That is the point of shipping them as notes
rather than as a document: a document has to be remembered and opened; a note
arrives by itself.

## What is here

| theme | lessons |
|---|---|
| **proof and checks** | 13 — including why a green check proves nothing until you have seen it fail |
| **measurement** | 9 — the instrument that contaminates its own reading, the average that describes nobody |
| **evidence and sources** | 5 — the citation that refutes your own conclusion, the copy that is not a second source |
| **data and identity** | 6 — one record one identity, the derived value that freezes when stored |
| **observability** | 7 — the read that answers 200 and is blind, the alert that invites an invented cause |
| **delivery and scope** | 5 — an inventory is not a deliverable, an approved sample is a debt |
| **agents and models** | 5 — author is not reviewer, model output is confirmed before it is persisted |
| **security** | 4 — a safety net never exercised is a belief, the guard with a blind window behind it |
| **tools and evaluation** | 2 — a roundup item is not a work item, "we already have one" is a quality verdict |

Start with [`the-check-that-passes-for-the-wrong-reason.md`](the-check-that-passes-for-the-wrong-reason.md).
It is the one the rest of this repository is built on.

## The honest limitation, stated up front

Every case in these notes is **reconstructed**. The lessons come from real
incidents; the stories illustrating them were rewritten with invented equivalents,
because the originals contain other people's operational detail that is not ours
to publish.

So: **the numbers here are illustrative, not measured.** Each note says so where
it tells a story. The lesson is what was carried across; the scenario is a vehicle
for it. Treat a figure in this folder as showing the *shape* of a failure, never
as a citation.

That is a deliberate trade, and stating it is not modesty — one of the notes here
is specifically about what happens when an unmeasured number gets presented as a
measured one.

## They are tested for reachability, not just written

A note that does not come back when the subject comes up is a document someone
has to remember to open — which is the thing these notes tell you not to build.

So reachability is checked: each lesson is queried with the natural question
someone would actually type, with **all 56 competing against each other**.
Current result: **55 of 56 return in first place**, one in second (two notes
genuinely answer the same question).

The failures that this test found were real and worth keeping in mind if you add
your own:

- The search is **lexical, with no stemming**. One note said *"four is a
  confession"* and the question said *"the fourth time"* — different terms, and
  the note was unreachable. Fixed by writing the vocabulary people actually use
  into the `description`, which is indexed alongside the body.
- Two notes covering adjacent ground **compete for the same slot**. That is not a
  defect, but it means the top result for an ambiguous question is a coin toss
  between two correct answers.

## Adding your own

Frontmatter that the engine needs:

```markdown
---
name: short-kebab-case-name
description: One or two sentences. This is indexed — put the words someone would
  actually type when they have this problem.
scope: global
type: concept
---
```

`scope: global` is what makes a note travel across projects. Without it, the
lesson stays trapped in the project where it was written.

**Write the description last, and write it as the question, not the title.** It is
the single highest-leverage line in the file for whether the note is ever seen
again.
