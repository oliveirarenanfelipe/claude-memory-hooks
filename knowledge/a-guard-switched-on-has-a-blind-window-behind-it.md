---
name: a-guard-switched-on-has-a-blind-window-behind-it
description: Any guard comparing against history — dedup, idempotency, 'already sent', a rate counter — is blind to everything before the moment it was switched on, unless the state was seeded.
scope: global
type: concept
---

# A guard switched on has a blind window behind it

**The rule.** Every guard that works by comparing against **recorded history** —
deduplication, idempotency keys, "already processed", a rate counter — knows
nothing about what happened before it started recording.

The window is not a bug in the guard. It is the guard behaving exactly as
designed, on an empty history.

## The shape of the failure

A deduplication check is added after a batch of duplicate messages goes out. It is
correct, it is tested, and from the moment it is enabled no duplicate passes.

Then everything sent **before** it existed gets processed again — because as far
as the guard knows, none of it happened. The very incident that motivated the
guard is repeated by the guard's first run.

*(Illustrative case.)*

## The rule that follows

**A history-based guard is switched on together with a seeding of its state**, or
with an explicit cutoff that makes it ignore everything before it existed.

Two options, and choosing is required:

- **Seed it** — backfill the history from whatever record exists. Slower, correct.
- **Cut off** — anything before timestamp T is treated as handled. Faster, and it
  must be written down, because "we do not know about anything before March" is
  something the next person needs to be told.

What is never acceptable is switching it on with an empty store and no decision,
which is what happens by default.

## Where else the blind window appears

- a rate limiter deployed mid-day, allowing a full quota again
- a "notify once" flag added to records that were already notified
- a lock introduced while a long operation is already running
- any counter that starts at zero on deploy

**Anything with memory has a birthday, and the day it was born it knows nothing.**
