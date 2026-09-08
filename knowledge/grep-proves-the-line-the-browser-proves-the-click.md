---
name: grep-proves-the-line-the-browser-proves-the-click
description: Evidence has levels, and the level has to match the claim. Finding the code proves the code exists; it does not prove the behaviour happens.
scope: global
type: concept
---

# Grep proves the line; the browser proves the click

**The rule.** Evidence comes in levels, and the level of your evidence has to
match the level of your claim.

| what you did | what it proves |
|---|---|
| found the line in the source | the code exists |
| the function is called in a test | that path executes under test conditions |
| the request appears in the log | it ran in this environment |
| you clicked it and watched | the behaviour happens for a user |

Each row proves everything above it and **nothing below it**.

## The shape of the failure

Someone asks whether the tracking fires on the checkout button. You grep, find
the handler, see the call, and answer yes.

The handler is bound to a selector that stopped matching when the markup changed.
The code is there, correct, and never runs. Everything you verified was true.

*(Illustrative case.)*

## Why the mismatch is so easy

Because the cheap evidence is genuinely evidence — it is not nothing, and it
usually correlates with the truth. The failure mode is not believing something
false; it is **stopping at a level and reporting as though you had reached a
higher one**.

## The practice

State the level with the claim. "The handler exists and is bound at line 40"
costs nothing extra to write and is honest. "The tracking works" is a claim about
the browser, and it needs a browser.

When the claim matters — money, data loss, something going to a third party —
climb to the level where the user is.
