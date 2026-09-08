---
name: the-average-is-not-the-typical
description: Using the mean as if it described typical behaviour produces a wrong diagnosis carrying a correct number. In a skewed distribution the median tells a different story and the decision changes.
scope: global
type: concept
---

# The average is not the typical

**The rule.** The mean describes the distribution's centre of mass, not its
typical member. In anything skewed — and most human behaviour is skewed — the
mean is dragged by a small tail and stops describing anyone at all.

## The shape of the failure

An analytics tool reports **average scroll depth: 22.6%** on a sales page. The
price sits at 16% of page height. The conclusion writes itself: people see the
price, scroll a little further, and leave. So the problem is the order of the
page — move the price down.

That conclusion was recorded in three places and a decision was built on it.

Then someone pulled the per-session distribution:

| | value |
|---|---|
| mean scroll | 22.6% |
| **median** | **3%** |
| sessions under 5% | **74%** |
| sessions past 16% | **21%** |
| median active time | **1 second** |
| sessions with zero active time | **45%** |

**Three out of four people never get near the price.** The 22.6% was manufactured
by a handful of sessions that read the whole page. The correct diagnosis is not
"the price appears too early" — it is "the click never engaged", which is a
traffic problem, not a page problem, and leads to entirely different actions.

*(Illustrative case.)*

## Why the wrong diagnosis is so persuasive

Because the number is **correct**. Nobody made an arithmetic error, the tool did
not malfunction, and the figure survives any audit that asks "is this number
right?". It fails only the question nobody asked: *right about what?*

## The practice

Whenever a single number is about to become a decision:

1. Ask for the **median** alongside the mean. If they disagree, the mean is not
   describing behaviour.
2. Ask what fraction sits below the threshold you actually care about. That
   fraction is usually the real finding.
3. Be suspicious of any average over a quantity with a hard floor and no ceiling
   — time on page, revenue per customer, response latency. Those are skewed by
   construction.

## The one-line version

A number can be accurate and still be about nobody.
