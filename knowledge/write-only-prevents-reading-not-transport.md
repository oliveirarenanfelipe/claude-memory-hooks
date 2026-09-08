---
name: write-only-prevents-reading-not-transport
description: A write-only secret cannot be READ back — but it can be transported, encrypted, by whoever already holds it. Declaring impossible at the first obstacle is stopping too early.
scope: global
type: concept
---

# Write-only prevents reading, not transport

**The rule.** A secret stored write-only — a CI secret, a platform vault — cannot
be read back through the interface that stores it. That is the guarantee, and it is
real.

It does **not** follow that the value is unreachable. Whoever already holds it can
still move it: encrypted, through a channel they control, into another system.
Those are different questions, and answering the first one closes an investigation
that had not started.

## The shape of the failure

A task requires a credential that exists only inside a platform's secret store.
The interface offers no read. The conclusion is recorded: it cannot be retrieved,
the task is blocked.

The question that reopened it was not technical: *"who already has this value?"* —
and there was an answer. The process that consumes the secret has it at runtime,
and could hand it, encrypted, to somewhere else.

*(Illustrative case.)*

## The general shape of the mistake

**A measured obstacle is not the absence of a path.** Verifying that one route is
closed is genuine work, and reporting it as "impossible" silently converts a fact
about one interface into a claim about the whole problem.

## The two questions before declaring something impossible

1. **Who or what already has this?** Access almost always exists somewhere; the
   question is whether it can be routed, not whether it exists.
2. **Is there an indirect delivery?** Not reading, but forwarding, mirroring,
   re-deriving, or asking the holder to push rather than pulling yourself.

## The honest phrasing while you are still looking

> *"I could not do it through X, because Y. I have not yet checked whether Z has
> it."*

That sentence keeps the investigation alive and is exactly as truthful as
"impossible", which closes it.

## The obligatory caveat

Sometimes the barrier is deliberate and moving the secret would defeat it. Then
the answer is still not "impossible" — it is **"possible and not allowed"**, which
is a decision for a person, not a technical conclusion.
