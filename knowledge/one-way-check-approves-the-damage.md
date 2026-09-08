---
name: one-way-check-approves-the-damage
description: A check that only measures the direction you are pushing will APPROVE the harm the same change causes on the other side. Every correction that moves a value needs a pair of checks.
scope: global
type: concept
---

# A one-way check approves the damage

**The rule.** Any correction that pushes a value in one direction needs **two**
checks: the one that measures whether it improved, and the one that measures
**the harm that same correction causes on the other side**. A single check is not
neutral — it *approves* the damage, and stamps it as measured.

## The shape of the failure

A photo comes back too dark: average brightness 89 on a 0-255 scale. You
multiply every pixel by a constant, write the obvious check, and it passes:

    assert brightness_after >= 150      # 89 -> 159. Green.

The picture is now a white blur. Multiplying scales every pixel by the same
factor, so the window — already near 255 — saturates and takes the wall with it.
**You shipped something worse than the original, with a number proving it got
better.**

The fix was two things, and the second matters more than the first. Changing the
operation (gamma, which lifts shadows and barely touches highlights) improved the
result. Adding the second check is what made the improvement *provable*: percent
of pixels at or above 250, with a ceiling. With both, brightness went 83 to 131
and blowout went 0.1% to 0.7%. The first check alone would have kept approving
the burnt version forever.

*(Illustrative case; the numbers show the shape, not a measurement.)*

## Why one check feels sufficient

Because you wrote it while thinking about the problem you were fixing. The check
inherits your framing, so it can only see the axis you were already worried
about. That is precisely why it cannot catch you.

## The question that generates the missing check

> **"What is a way to hit this target and still deliver something worse?"**

Ask it before writing the assertion, not after. The answer is the second check.

## Where it generalises

- Performance: latency down, memory up.
- Recall: more results returned, precision destroyed.
- Compression: file smaller, artefacts everywhere.
- Copy: shorter, and the meaning is gone.

Any time an optimisation has a knob, the knob has two ends. A test suite that
only holds one end is holding the wrong thing.
