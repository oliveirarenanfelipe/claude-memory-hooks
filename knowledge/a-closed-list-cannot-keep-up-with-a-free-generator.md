---
name: a-closed-list-cannot-keep-up-with-a-free-generator
description: A fixed lookup table that must recognise the output of something that generates freely will always be behind. Adding a row fixes the case and never the class.
scope: global
type: concept
---

# A closed list cannot keep up with a free generator

**The rule.** When a fixed table has to recognise the output of something that
**generates freely** — a model, a user typing, an external system evolving — the
table is permanently behind. Every unrecognised value produces one more row, which
fixes that case and leaves the class untouched.

## The shape of the failure

A mapping translates incoming category labels into internal ones. The source of
those labels starts producing variations: synonyms, different casing, a new value
nobody announced.

Each mismatch is reported, and each is fixed by adding a row. The table grows
steadily, the failures never stop, and the work feels like maintenance rather than
like a design problem.

*(Illustrative case.)*

## The tell

**You have added rows to the same table three times for the same reason.** Not
three unrelated new categories — three variations of things you already had.

## The three ways out, in order of preference

1. **Constrain the generator.** If you control the producing side, make it emit
   from a closed set. This is by far the cheapest fix and is usually dismissed too
   early because the producer belongs to someone else — worth asking anyway.
2. **Recognise the class instead of the value.** Match on a normalised form, a
   pattern, a rule — anything that covers values you have not seen. The table stops
   being an enumeration and becomes a definition.
3. **Make unknown a first-class outcome.** If neither is possible, unknown values
   must route somewhere visible rather than falling into a default. A default
   silently absorbs the class and you stop learning it exists.

## The failure to avoid above all

**Mapping unknown to a plausible default.** It removes the error, keeps the data
wrong, and destroys the only signal you had.
