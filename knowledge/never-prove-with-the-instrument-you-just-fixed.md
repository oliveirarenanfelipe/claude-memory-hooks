---
name: never-prove-with-the-instrument-you-just-fixed
description: After repairing a counter that was lying, that same counter cannot be the evidence that it now works. The proof has to come from outside what you touched.
scope: global
type: concept
---

# Never prove with the instrument you just fixed

**The rule.** When the thing that was wrong is the **measuring device**, its own
output cannot be the evidence that it is now right. The proof has to come from
outside whatever you touched.

## The shape of the failure

A counter has been reporting the wrong totals. You find the bug, fix it, run it
again, and it now reports a number that looks correct. You report the fix as
verified.

But the only evidence you have is a number produced by code you just edited, and
the property you are claiming — *this number is now correct* — is exactly the
property that was broken. The new number being plausible is not evidence; the old
number was also plausible.

*(Illustrative case.)*

## What counts as outside

- counting the same thing by a different route (a query instead of the script)
- a fixed input with a known answer, computed by hand once
- a second implementation, however crude, that only exists to disagree
- for a small enough case, literally counting by eye

## The related trap

**Two measurements sharing the same formula agree because they make the same
mistake.** Agreement to four decimal places is a sign of shared code, not of
correctness. Independent verification means an independent path — if both numbers
come from the same function, you have one measurement printed twice.

## The question to ask

> **"If the fix were wrong, what would I see right now?"**

If the answer is "the same thing I am seeing", you have no evidence yet.
