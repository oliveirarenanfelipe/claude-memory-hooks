---
name: a-signal-inherits-the-position-of-the-layer-it-lives-in
description: A layer created for logging sits wherever it was convenient. Graft a signal that DECIDES onto it and the signal inherits that position — written after whoever reads it.
scope: global
type: concept
---

# A signal inherits the position of the layer it lives in

**The rule.** A layer that exists for **observation** — a log line, a debug
record, an audit trail — has an arbitrary position in the flow, because nothing
depended on when it happened. The moment someone grafts onto it a value that
**decides** something, that value inherits the arbitrary position.

## The shape of the failure

A record is written at the end of a handler, for tracing. Later, a feature flag
is stored on the same record because the plumbing was already there.

The flag is now written **after** the code that reads it. The flag is on, the
trace shows it on, and behaviour never changes. Everything is correct except the
order, and nothing about the flag's own code looks wrong.

*(Illustrative case.)*

## Why it survives review

Both halves are individually sensible. The logging is where logging belongs; the
flag is stored with related data. The defect exists only in the relationship, and
nobody reviews relationships between a logging change and a behaviour change made
months apart.

## The question that catches it

> **"Does anything READ this before this line runs?"**

Ask it whenever a decision value is added to an existing structure. If yes, the
value needs its own position, not the inherited one.

## The general form

**Observation may happen at any time; decision may not.** The moment a field
crosses from one category to the other, its timing becomes a contract — and
nothing in the code marks that crossing. Naming it explicitly is the cheapest
protection available.
