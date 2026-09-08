---
name: pushed-tolerates-staleness-pulled-does-not
description: The same data carries different freshness contracts depending on who started the exchange. A report you push is understood as a snapshot; an answer someone pulled reads as 'right now'.
scope: global
type: concept
---

# Pushed tolerates staleness; pulled does not

**The rule.** The same number carries a **different freshness contract** depending
on who initiated the exchange.

| | the implicit promise |
|---|---|
| **pushed** — a report, a digest, a scheduled alert | *"this is the picture as of when I was sent"*, and everyone reads it that way |
| **pulled** — someone asked a question | *"this is now"* |

Serving stale data to someone who asked makes the system lie, and lie with
authority, because the answer arrives in response to a live question.

## The shape of the failure

A batch job computes a status summary every morning at eight. It works well: the
digest goes out, people read it, and everyone understands it describes the state
at eight o'clock.

Then a conversational interface is added, so people can ask about status directly.
The obvious implementation reuses the eight o'clock summary — the data is right
there, already computed.

Now someone asks at four in the afternoon and is told about work that was
completed at ten. They chase something already finished. From their side there is
no signal at all that the answer is old, because they asked *now*.

Recomputing live cost **3.8 seconds**. The cached answer could be up to **48 hours**
behind on a weekend.

*(Illustrative case; the shape is what matters.)*

## The design consequence

**A pull path needs its own freshness decision, separate from the push path that
fed it.** Reusing the batch output is the natural implementation and is usually
wrong. Either recompute, or state the age in the answer — "as of 08:00 today" —
and let the reader decide.

Stating the age is cheap and almost always sufficient. Saying nothing is what
turns stale into false.

## Where else it bites

- A dashboard someone opens on demand, backed by a nightly table.
- A support tool answering "what is this customer's balance" from a replica.
- Any cache whose acceptable age was chosen for the writer's convenience and never
  re-examined from the reader's side.
