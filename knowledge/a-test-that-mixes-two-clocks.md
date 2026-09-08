---
name: a-test-that-mixes-two-clocks
description: A test that builds its fixture at a frozen time and then crosses code reading the real clock is born green and turns red on its own, days later, with nobody touching anything.
scope: global
type: concept
---

# A test that mixes two clocks

**The rule.** If a test constructs its data at one notion of "now" and the code
under test reads a different one, the test is not deterministic — it is
**time-bombed**. It passes today and fails on a date nobody chose.

## The shape of the failure

A fixture is built with a frozen timestamp so the assertions are stable. The
function it calls computes an age using the real system clock. On the day it is
written the two are close enough and everything passes. Four days later the
difference crosses a threshold and the suite goes red with no commit in between.

The debugging that follows is expensive out of all proportion, because the first
question everyone asks — *what changed?* — has the answer **nothing**, and that
answer sends people looking in the wrong place for hours.

*(Illustrative case.)*

## The rule that prevents it

**One clock per test.** Either freeze both sides or freeze neither. If the code
reads the real clock, the test must inject it rather than pretending.

## The tell you already have

A test that fails without a commit is almost always one of three things: a clock,
a shared resource, or an ordering dependency. All three are the same underlying
defect — **the test depends on something it does not declare**.

## The cheap check

Run the suite with the system date set forward a week. Anything that goes red was
depending on today.
