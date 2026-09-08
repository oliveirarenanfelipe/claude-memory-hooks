---
name: an-alert-without-evidence-invites-an-invented-cause
description: An alert that says something is wrong without saying WHAT forces whoever reads it to supply a cause from imagination — and a plausible invented cause is accepted and acted on.
scope: global
type: concept
---

# An alert without evidence invites an invented cause

**The rule.** An alert that reports a problem without carrying the evidence of
**which** thing is wrong forces the reader to supply the cause from imagination.
People are good at plausible causes, so the invented one gets accepted, recorded,
and acted on.

## The shape of the failure

A detector writes one line whenever a monitored item does not appear where it
should:

    WARN: 1 item missing from the dashboard

Nothing about which item, of what kind, belonging to whom. Nineteen of these
accumulate. Triage reads them, notices that a monthly report had been failing
around the same period, and attributes all nineteen to that report. It is
coherent, it fits the timeline, and it is written down as the cause.

When someone finally instruments the detector to record **what kind of thing** was
missing, the answer is different: eight customers had received no report at all.
Not a rendering problem — an entire class of delivery that never happened.

*(Illustrative case.)*

## Why "do not guess the cause" does not work as a rule

Because the rule addresses the reader, and the defect is in the writer. Being
told not to speculate does not help when the alert contains nothing else to work
with — the alternative to speculating is doing nothing, and the alert exists
precisely to make someone act.

## The fix has a mandatory order

1. **First**, the instrument carries the identity of what it saw: the kind, the
   id, the owner, the value.
2. **Only then** can any rule about not inventing causes have anything to bite on.

Doing it in the other order — writing the rule first — produces a rule that is
violated by the same person who wrote it, because the situation offers no way to
comply.

## The test for an alert you are about to ship

> **"Reading only this line, can someone name the specific thing that is wrong?"**

If not, it is not an alert. It is a prompt for a story.
