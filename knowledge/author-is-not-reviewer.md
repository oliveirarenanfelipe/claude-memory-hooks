---
name: author-is-not-reviewer
description: Multi-agent discipline that survives contact: the author never reviews their own output, writes are allow-listed by role, three failures halt, and a handoff carries its acceptance condition.
scope: global
type: concept
---

# Author is not reviewer

Four rules for coordinating several workers — human or automated — that hold up
under real conditions. They are unglamorous and each one exists because its
absence is expensive.

## 1. The author never reviews their own output

Whoever produced something cannot see what is missing from it — they supply the
gap from memory every time they read. This is not a discipline problem, it is not
available to them.

With automated workers this is easy to get wrong, because the same worker is
cheap to reuse and *knows the context*. Knowing the context is precisely the
disqualification.

The reviewer must start from the artefact, not from the conversation that
produced it.

## 2. Write access is allow-listed by role

A worker that can write anywhere will eventually write somewhere surprising, and
the trace of why will be gone. Declare, per role, which paths may be written.
Anything outside is refused rather than logged — a log nobody reads is the same
as no restriction.

## 3. Three failures halt

A worker that fails the same step three times is not going to succeed on the
fourth. It will, however, keep consuming budget and producing plausible partial
output that someone downstream will treat as finished.

Halt, report the three attempts, and hand it to a person. **The number matters
less than having one.**

## 4. A handoff carries its acceptance condition

"Pass this to the next stage" is not a handoff. **"Pass this on when the output
contains X and Y"** is. Without the condition, the receiving stage starts work on
whatever it is given, including the failed attempt, and the failure propagates
with a clean face.

## Why these four and not more

Each one closes a way for work to look complete when it is not. That is the entire
risk in delegated work: not that a step fails, but that a failed step is
indistinguishable from a finished one to whoever is next.

*(No case study here: this note is a rule, not a story. Where other notes
in this folder show a scenario, the scenario is illustrative.)*
