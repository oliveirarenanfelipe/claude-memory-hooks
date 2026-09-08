---
name: the-instrument-contaminates-the-measurement
description: Measuring by WRITING into the system you are measuring leaves residue: the first reading is honest, the ones after it lie — and they lie as false negatives, which are the convincing kind.
scope: global
type: concept
---

# The instrument contaminates the measurement

**The rule.** If your probe writes into the system it is measuring, the first
reading is honest and every reading after it is about the residue. Restore the
state after each probe, or measure on a copy.

## The shape of the failure

You want to know whether a queue processes duplicate submissions. You submit a
test record and watch. It goes through. You submit again to confirm — and this
time it is silently dropped.

The obvious conclusion is that de-duplication works. The real explanation is that
your first probe **created the very record** the second probe collided with. You
measured your own footprint.

The reason this is dangerous rather than merely wrong: the contaminated reading
almost always comes back as a **false negative** — "that path does not exist",
"nothing happens here", "the handler is not reached". Absence is convincing.
Nobody demands evidence for a road that is not there.

*(Illustrative case; the shape is the point.)*

## The cheap test

**Re-run the FIRST probe at the end.** If it now gives a different answer than it
gave at the start, the instrument is dirty and every conclusion drawn in between
is suspect.

It costs one extra run and it is the only check that catches this class without
knowing in advance what the residue is.

## What counts as writing

More things than you would expect:

- inserting a row, obviously
- sending a request that increments a counter or a rate limit
- opening a file in a mode that truncates it
- anything that advances a cursor, a sequence, or an offset
- reading, when reading marks something as read

If the probe changes what the next probe will see, it is a write.
