---
name: the-third-occurrence-is-a-count-not-a-fix
description: Fixing the same class of defect case by case feels like progress and leaves the cause untouched. When it returns wearing a different face, the deliverable stops being the fix and becomes the count. The second, third and fourth time you fix the same thing in a different file: stop repairing case by case and count the class instead.
scope: global
type: concept
---

# The third occurrence is a count, not a fix

**The rule.** When the same class of defect appears a third time, **stop fixing
it**. The deliverable is no longer the repair — it is the **census**: how many
instances exist, what they have in common, and what single change removes the
class.

## Why case-by-case is so seductive

Every individual fix works. It is small, verifiable, and produces a visible
result. That feeling of progress is exactly what keeps the underlying cause
untouched, and each fix makes the next occurrence slightly less surprising —
until nobody registers them as related at all.

The defect also changes appearance. The same root cause surfaces as a display
problem, then a calculation problem, then a delivery problem, and the pattern is
invisible unless someone deliberately lines them up.

## The shape of the failure

Four occurrences in a week, each fixed within an hour, each in a different file.
Only when someone finally asked *"how many of these have there been?"* did the
shared cause appear — a single normalisation that was missing from a shared
accessor, compensated for locally in four places.

The fix, once identified, was three lines.

*(Illustrative case.)*

## The moment to switch, and how to recognise it

**Two is a coincidence. Three is a pattern. Four is a confession.**

The signal is not "this is hard". It is *"I have written something like this
before"*. That thought is the trigger, and it arrives reliably — it is simply
overridden, because finishing the fix in front of you takes ten minutes and
counting takes an afternoon.

## What the census looks like

1. Grep for the shape, not the symptom. The symptoms differ; the shape does not.
2. Count. The number is the deliverable, and it is almost always larger than
   anyone expected.
3. Name the single place that would have prevented all of them.
4. Fix that, and delete the local patches — leaving them means the next person
   cannot tell which layer is responsible.
