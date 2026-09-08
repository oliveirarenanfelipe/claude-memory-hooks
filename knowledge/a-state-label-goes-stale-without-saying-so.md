---
name: a-state-label-goes-stale-without-saying-so
description: A note describing STATE — what a page serves, whether a job runs, whether a token is alive — ages silently and keeps reading as fact long after it stopped being true.
scope: global
type: concept
---

# A state label goes stale without saying so

**The rule.** There are two kinds of written claim, and they age completely
differently:

- **A rule or a finding** — *"multiplying brightness saturates highlights"* — stays
  true.
- **A state** — *"this job runs nightly", "this token is valid", "this page serves
  the new layout", "the client approved it"* — is a **photograph**, and it starts
  decaying the moment it is written.

Both look identical on the page. Neither carries an expiry. And the state one
keeps reading as a present-tense fact forever.

## The shape of the failure

A sweep through a set of internal notes finds a substantial fraction of the
state-describing claims no longer true: schedules that were disabled, endpoints
that moved, integrations switched off, approvals that were later withdrawn.

Not one of them was wrong when written, and not one had announced anything.
Meanwhile decisions had been made on top of them.

*(Illustrative case.)*

## Why this is worse than a plain error

An error can be caught by review. A stale state claim was **correct at review
time**, so no amount of care at the moment of writing prevents it. The defect is
introduced by the passage of time, which no reviewer is present for.

## The practice

1. **Date every state claim, inline.** *"as of March, the job runs nightly"*. It
   costs four words and converts a false statement into a true one — the reader
   can now judge the age themselves.
2. **Prefer a pointer to a value.** *"the schedule is in `deploy/cron.yaml`"* never
   goes stale. Copying the schedule into prose does.
3. **When you read a state claim while working, verify it or mark it.** You are the
   only person who will ever be in a position to.

## The one-line test

> **"Could this sentence become false without anyone editing this file?"**

If yes, it needs a date, or it should be a pointer instead.
