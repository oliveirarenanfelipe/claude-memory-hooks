---
name: blind-review-with-a-declared-prediction
description: To judge something you wrote, give a real task to someone with no context and only your artefact — and write down what you expect to happen BEFORE they start. How to tell whether a document, a README or an interface is understandable to someone else: hand it to a reader with no context and write your prediction down first.
scope: global
type: concept
---

# Blind review with a declared prediction

**The technique.** To find out whether something you wrote actually works — a
document, an interface, an API, an instruction — give a **real task** to someone
with **no context**, whose only resource is the artefact. And write down what you
expect to happen **before** they start.

## Why the author cannot do this alone

Whoever wrote it knows what it means. Re-reading, you supply from memory every
piece that is missing from the page, and you cannot stop doing that. This is not
carelessness; it is not available to you at all.

The blind reader supplies nothing. What they cannot do is precisely what is not
in the artefact.

## Why the prediction matters as much as the test

Without it, whatever happens gets absorbed: they struggled here, well, that part
is admittedly tricky; they misread that, they were going too fast. Every outcome
becomes compatible with the artefact being fine.

**A written prediction cannot be revised afterwards.** The gap between what you
expected and what happened is the finding, and it only exists if you wrote the
expectation down first.

## The shape of it

    Prediction, before the run:
      - they will find the entry point in under a minute        -> they did, 20s
      - they will need the config section for step 3            -> they did
      - they will NOT need to ask anything                      -> they asked twice

Two questions asked. Both about a step described in a sentence the author
considered obvious. That sentence is the finding, and no amount of re-reading by
the author would have produced it.

*(Illustrative case.)*

## Scaling it down

You do not need a person. Any competent reader with no context works — a
colleague from another team, or an assistant given only the artefact and the task.
The requirement is not intelligence. It is **absence of your context**.
