---
name: one-record-one-identity
description: When the same real-world entity can be written two ways and neither is declared the owner, the system carries two entities. It shows up one patch at a time — and patch N+1 is the signal.
scope: global
type: concept
---

# One record, one identity — and patch N+1 is the signal

**The principle.** If the same real-world entity (a person, a customer, a tenant,
a device) can be written in more than one form, and **none of the forms is
declared the canonical one**, your system now contains two entities. It does not
fail all at once. It fails **one place at a time**, and each failure looks like an
isolated case asking for a local patch.

**The signal that the cause is identity and not the case in front of you:** you
are writing the **N+1th patch** for the same subject, in another file. Three is a
pattern. Four is a confession.

## The shape of the failure

A phone number has two written forms: the long one your signup form stores, and a
shorter legacy form that the messaging provider actually delivers to. Neither is
declared the owner. What that produced, before any fix:

- 350 records for 252 people
- 98 people holding two records each
- 33 pairs where **both** records had already been messaged
- 198 duplicate messages sent to real people

Each of those was discovered separately, and each one had a plausible local
explanation at the time.

*(Illustrative case; the counts show the shape.)*

## Why local patches feel right and make it worse

Every patch is small, targeted and demonstrably fixes the case in front of you.
That is exactly the problem: it works, so it ends the investigation. Meanwhile the
number of places that must agree about identity keeps growing, and each new one
starts out wrong.

## The cure has a location

**Canonicalise inside the shared accessor** — the one function through which
every read and write of that entity passes. Not at the call sites. Not in a
cleanup job. The moment two call sites do their own normalisation, they will
drift, and the drift is silent.

If there is no shared accessor, that is the actual finding, and building one is
the fix.

## What to check when you suspect it

1. List every place the entity is looked up. If it is more than one function,
   ask why.
2. Count distinct records against distinct real entities. A ratio above 1.0 is
   the whole diagnosis.
3. Look for the patches. They are the map: each one marks a place that had to
   compensate for the missing owner.
