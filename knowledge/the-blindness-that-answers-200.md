---
name: the-blindness-that-answers-200
description: Separating 'failed' from 'empty' is not enough. A read can succeed, return 200, and hand back content that is not what the code thinks it is — no exception, no status, no null to test.
scope: global
type: concept
---

# The blindness that answers 200

**The rule.** Guards usually cover two ways of not seeing: the call **failed**, and
the call returned **nothing**. There is a third that neither covers:

> **The read works. It answers 200. And the content is not what the code thinks
> it is.**

No exception to catch, no status to check, no null to test. The success path runs
end to end, with a false result.

## Two faces of it

**1. The format changed underneath.** A membership list starts arriving with a new
kind of identifier. The parser only accepts the old shape, returns null for all
41 entries, and the function reports **success with an empty list** — the exact
thing its own contract promises never to do. Downstream falls back to a proxy
metric and reports a plausible number for days. Nothing is red anywhere.

The identifier had not disappeared. It was in an adjacent field the parser never
looked at.

**2. The data aged.** An upstream table stopped being written at 09:35 one
morning. A watchdog reading it ran **48 consecutive times in green**, reporting
"all calm, zero activity today". The detector it was supposed to be watching was
dead, and the job was green the whole time.

*(Illustrative cases.)*

## What the two have in common, and it is the rule

**Non-empty input producing empty output is a broken read, not a real answer.**
And a source that can freeze needs the **age of the data** checked, not just its
presence. Both are the same discipline: a successful call is not a verified
answer.

## The three guards, in order of how often they are missing

1. **failed** — almost always present
2. **empty** — usually present
3. **empty result from non-empty input** — almost never present, and it is the one
   that produces confident wrong numbers
4. **the data is old** — never present until someone gets burned

## The cheap version

Where a read can return a list, assert the relationship between input and output,
not just the output: *if I passed 41 identifiers in, zero results out is an error,
not an answer*. And where a source can stall, carry a timestamp and check it.
