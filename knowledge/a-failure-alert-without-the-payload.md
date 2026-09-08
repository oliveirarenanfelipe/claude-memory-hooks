---
name: a-failure-alert-without-the-payload
description: An alert saying 'could not deliver' that carries only the identifier leaves the human unable to take over. The message exists, the channel is down, and nobody can reach the content.
scope: global
type: concept
---

# A failure alert without the payload

**The rule.** An alert reporting that something could not be delivered must carry
**the thing that was not delivered**, not just the fact and the recipient.
Otherwise the person who receives the alert cannot take over manually — which is
the only reason the alert exists.

## The shape of the failure

A delivery channel goes down. The system correctly notices, and sends an alert:

    FAILED: could not deliver notification to customer 4471 (channel timeout)

Everything is true and actionable-sounding. But the content of the notification
lives in a queue nobody can read from a phone, so the person on call knows a
customer is missing something and cannot say what.

The work of recovering it — find the queue, find the item, render it — takes long
enough that the alert effectively did nothing.

*(Illustrative case.)*

## The test for an alert about a failed action

> **"Can the person receiving this complete the action by hand, using only what is
> in front of them?"**

If not, the alert reports a problem and withholds the solution.

## What to include

- what was supposed to happen, in full — the text, the payload, the amount
- who it was for
- why it failed
- what the person should do, explicitly, including "nothing, it will retry"

The last one matters more than it looks: an alert that does not say whether it
will retry forces the reader to investigate before they can decide to ignore it.

## The size objection

Payloads can be large. The answer is a link to somewhere reachable, not omission
— and "reachable" means reachable from where the person actually is when the
alert arrives, which is rarely at a desk.
