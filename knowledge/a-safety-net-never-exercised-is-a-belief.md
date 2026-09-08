---
name: a-safety-net-never-exercised-is-a-belief
description: A fallback that has never actually been triggered is not a safety net — it is the belief that one exists. It fails on precisely the day it is needed.
scope: global
type: concept
---

# A safety net never exercised is a belief

**The rule.** A fallback, a retry path, a reconciliation job, a restore procedure
that has **never actually run in anger** is not a safety net. It is the belief
that one exists — and beliefs fail on the day they are called.

## Why untested recovery paths are worse than average code

Three reasons compound:

1. **They are written under optimism.** The fallback is built while thinking about
   the happy path, by someone who has not yet seen the failure it is for.
2. **They never run**, so they rot silently — a renamed field, a changed
   permission, a dependency removed. Nothing exercises them, so nothing reports it.
3. **They run for the first time during an incident**, which is the worst possible
   moment to discover a bug, when attention and time are already gone.

## The shape of the failure

A restore procedure is documented and a backup runs nightly, verified by checking
the file exists and is roughly the right size. During a real incident the restore
fails: the backup contains the data but the procedure references a tool version
that no longer exists on the host.

The backup was fine the whole time. The **path back** was never walked.

*(Illustrative case.)*

## The practice

**Exercise it on a schedule, on purpose, when nothing is wrong.**

- restore the backup into a scratch environment, monthly, and check a known record
- force the fallback path with a flag and confirm the output is correct, not just
  that it does not crash
- kill the primary and watch the secondary take over, at a time you chose

## The line that decides

> **"When did this last run successfully, and how do I know?"**

If the answer is "it hasn't had to", you do not have that capability yet. You have
an intention, and the difference will only become visible at the worst moment.
