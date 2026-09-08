---
name: what-is-not-measured-disappears-quietly
description: Every gate covers what someone thought to measure. What falls outside does not announce itself when it breaks — it simply vanishes, and the report still says APPROVED.
scope: global
type: concept
---

# What is not measured disappears quietly

**The rule.** A gate covers exactly what someone thought to check. Everything
outside that set does not fail loudly when it breaks — **it disappears**, and the
report still says approved.

Absence has no error code. That is the entire problem.

## The shape of the failure

A pipeline is guarded by checks on duration, file count and output size. All three
pass. Six separate defects ship in one day: a missing audio track, a caption never
rendered, a frame range dropped, a language variant that stopped generating, an
overlay that silently failed, a file written to the wrong folder.

Every one of them was outside the three properties being measured. The run
reported APPROVED six times.

*(Illustrative case.)*

## Why more assertions is not the fix

You cannot enumerate your way out of it — the missing check is by definition the
one you did not think of. Adding checks helps, and it never closes the gap.

## The two things that do help

**1. Compare against the previous run, not against a threshold.** A diff notices
things nobody named: the output is 4% smaller, there are two fewer files, this
field is now absent. A drift check catches unknown unknowns because it does not
need to know what to look for.

**2. Sample the actual output, by eye, on a schedule.** Not every run — one in
twenty. The purpose is not verification; it is discovering what your checks do
not cover, which is the only way that list ever shrinks.

## The honest framing for a green report

"Approved" means *"the things I check are within range"*. It never means "this is
correct". Writing it the first way in your own reports changes how they are read,
including by you.
