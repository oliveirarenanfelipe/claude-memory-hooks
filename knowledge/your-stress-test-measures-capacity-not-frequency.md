---
name: your-stress-test-measures-capacity-not-frequency
description: A scenario you construct measures what the system can withstand, not how often the problem occurs. Sizing the solution from it justifies a large build for a small pain.
scope: global
type: concept
---

# Your stress test measures capacity, not frequency

**The rule.** A scenario you construct to break something tells you **what the
system can withstand**. It tells you nothing about **how often that situation
arises**. Sizing a solution from the first number while believing it is the second
justifies large work for small pain.

## The shape of the failure

You build a load scenario and find that the queue collapses at a certain rate. The
finding is real and reproducible. A redesign is proposed to handle it.

Nobody measured the actual arrival rate in production. When someone finally does,
the observed peak is a fraction of the tested threshold and has never been
approached. The collapse is genuine and has never happened.

*(Illustrative case.)*

## The two numbers, and they are always both needed

| number | comes from | answers |
|---|---|---|
| capacity | the scenario you build | *how bad can it get?* |
| frequency | production data | *how often does it get there?* |

Capacity alone produces over-engineering. Frequency alone produces fragility. The
decision needs both, and the second is usually the one nobody has.

## Why capacity gets measured and frequency does not

Because capacity is available on demand — you construct it in an afternoon.
Frequency requires having instrumented the real system before you needed the
answer, which means it either exists already or it does not exist at all.

That asymmetry is worth planning around: **the cheap instrument to add today is
the one that counts how often, not the one that measures how bad.**
