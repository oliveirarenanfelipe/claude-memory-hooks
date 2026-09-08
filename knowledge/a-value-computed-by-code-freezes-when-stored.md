---
name: a-value-computed-by-code-freezes-when-stored
description: A value calculated by code and copied into stored state is not updated when the code is fixed. The fix heals new records and leaves the old ones sick — and the old ones are the ones being used.
scope: global
type: concept
---

# A value computed by code freezes when stored

**The rule.** When code computes something and the result is **written into
persistent state**, fixing the code fixes only what is computed from now on.
Every existing record keeps the old, wrong value — and existing records are
usually the ones in use.

## The shape of the failure

A field is derived at write time: a category, a normalised key, a total. A bug in
the derivation is found and corrected. New records are right. The fix is reported
as done.

The wrong values remain on every record created before the fix, and nothing in
the system distinguishes them. The bug reports keep arriving, now with the extra
confusion that the code is demonstrably correct — anyone reading it concludes the
report must be mistaken.

*(Illustrative case.)*

## Why the fix feels complete

Because you can reproduce the bug before and not after. That test is real and it
covers the *computation*. The **stored data** is a second population, and it was
never in the test.

## The rule that follows

**A fix to a derivation is not finished without a backfill** — or an explicit,
recorded decision not to backfill, with the reason.

The decision to skip it is often correct: the old records may be closed, or the
value may not matter historically. What is never acceptable is not deciding, and
the way that happens is simply never noticing there were two populations.

## The design lesson underneath

Every derived value written into storage is a **copy that can diverge from its
source**. Sometimes that is exactly what you want — a price at the time of sale
must not change. Often it is only convenience, and convenience buys you a
permanent obligation to keep two things in sync.

Ask which one you are doing, when you write it, and put the answer in a comment.
