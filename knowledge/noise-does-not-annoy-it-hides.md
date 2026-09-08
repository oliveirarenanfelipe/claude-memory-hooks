---
name: noise-does-not-annoy-it-hides
description: False alerts are not merely irritating: they conceal the real case inside them. Before counting how many alerts a system fires, count how many a person could CLOSE by doing work.
scope: global
type: concept
---

# Noise does not annoy — it hides

**The rule.** The cost of a false alert is not irritation. It is **concealment**:
the real case sits inside the pile, indistinguishable from the noise, and gets the
same amount of attention as the thirty things that did not matter.

## The shape of the failure

A system fires 31 open alerts. A dashboard shows the count and it looks healthy —
alerts are being generated, someone is presumably working them.

Going through them one at a time: **27 were already finished.** The work had been
done, completed and signed off. No human action could close them; the only way to
silence one was to open the record and touch it for no reason.

**The remaining 4 were scheduled site visits whose date had already passed** — by
11, 30, 44 and 60 days. A customer with an appointment, nobody showed up, nobody
called.

Those four were the entire product of the system. It is the most serious case the
data contains — a third party waiting, with a commitment made, with no follow-up —
and it was indistinguishable from twenty-seven notices about completed work.

*(Illustrative case.)*

## Why the usual metric misses it

A count of alerts fired measures **volume**, and volume is not the same as
justified. The question that separates them:

> **"What human work makes this alert go away?"**

If the answer is "none", or "editing the record to no purpose", the alert is false
by construction and is occupying the place of a true one.

## Two rules that follow

1. **Before counting how many alerts a system fires, count how many a person
   could CLOSE by doing actual work.** That second number is the only one that
   describes the system's value.
2. **When you find a false positive, measure what it was hiding.** Do not stop at
   removing it. The question *"and what was left?"* is where the finding is.

## The most common vector, worth naming

**A terminal state whose name does not sound terminal.** A record marked
`VALIDATED` sitting after `COMPLETED` in the workflow will be read by everyone —
including whoever writes the detector — as an intermediate step. The detector then
treats finished work as outstanding, forever, and nobody questions it because the
name sounds like a checkpoint.

Read the state machine, not the state names.
