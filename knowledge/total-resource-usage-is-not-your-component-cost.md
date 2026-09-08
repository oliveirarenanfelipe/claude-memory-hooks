---
name: total-resource-usage-is-not-your-component-cost
description: Reading total memory, disk or GPU usage and attributing it to the thing you just deployed inflates its cost by the entire baseline — and kills correct decisions.
scope: global
type: concept
---

# Total resource usage is not your component's cost

**The rule.** Reading a **total** — memory in use, disk consumed, GPU occupied —
right after deploying something, and attributing that total to the new thing,
inflates its cost by the whole pre-existing baseline.

## The shape of the failure

A service is deployed on a shared machine. The monitor shows high memory usage.
The number is recorded as the service's footprint, and it is large enough that a
plan to run several instances is abandoned.

The baseline before deployment was never captured. The actual increment was a
fraction of the total, and the abandoned plan was entirely feasible.

*(Illustrative case.)*

## Why it happens even to careful people

Because the total is what the tool shows you. Getting the increment requires
having measured **before**, and before is exactly when nobody is thinking about
measurement — the interesting moment is after.

## The practice

**Always measure the delta, and that means measuring first.**

1. Capture the baseline before deploying. One command, thirty seconds.
2. Deploy.
3. Capture again. The difference is your number.

If you forgot step 1, the honest options are to stop the component and measure
again, or to report the total **explicitly labelled as a total** — never as the
component's cost.

## The general form

Any measurement taken on a shared substrate needs a control. Response time on a
loaded machine, error rate during an incident, conversion during a campaign. The
question is never "what is the number" but **"what is the number compared to
what"**, and the comparison has to be captured at a moment that has already
passed by the time you want it.
