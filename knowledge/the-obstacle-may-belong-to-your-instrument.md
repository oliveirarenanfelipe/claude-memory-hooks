---
name: the-obstacle-may-belong-to-your-instrument
description: 'The site blocks automation' usually describes the browser you chose, not the site. A verdict about the target, when the cause is the instrument, becomes a permanent false constraint.
scope: global
type: concept
---

# The obstacle may belong to your instrument

**The rule.** When something does not work, the failure gets attributed to the
**target** — the site blocks this, the API forbids that, the format is not
supported. Often the true cause is the **instrument**: the specific client,
library, version or environment you happened to use.

The two produce identical symptoms and completely different futures.

## The shape of the failure

An automated login fails with a specific error. The conclusion recorded is that
the site blocks automation. A workaround is designed around that constraint —
scheduled retries, session keeping, extra infrastructure.

The site blocks *that browser build*. A different one, closer to what a person
actually runs, logs in immediately. The constraint never existed, and a system was
built to live with it.

*(Illustrative case.)*

## Why the wrong verdict sticks

Because it is written down as a fact about the world, and facts about the world do
not get re-tested. Every later decision inherits it. Nobody re-runs the original
experiment because the question is considered settled — and it was settled by a
single trial, with a single instrument.

## The cheap discrimination

**Change one thing about the instrument and retry.** A different client, a
different version, a different machine, a different network. If the behaviour
changes, the constraint was yours.

This costs minutes and it happens almost never, because by the time the workaround
is being designed the diagnosis feels like history.

## The practice for writing it down

When recording a constraint, record the instrument with it:

> *"Logging in fails with error X **using client A, version B**. Not retested with
> other clients."*

That sentence stays honest as it ages, and it tells the next person exactly which
experiment would overturn it. **"The site blocks automation"** tells them the
question is closed.
