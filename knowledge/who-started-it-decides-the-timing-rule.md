---
name: who-started-it-decides-the-timing-rule
description: A business-hours window protects against UNSOLICITED contact. So the right rule is not the clock — it is who initiated. A reply to someone's own action goes out immediately, at any hour.
scope: global
type: concept
---

# Who started it decides the timing rule

**The rule.** A quiet-hours window exists to protect people from **unsolicited**
contact. So the correct test is not what time it is — it is **who initiated the
interaction**.

| the interaction started with | when it may go out |
|---|---|
| the person (they signed up, bought, asked, replied) | **immediately**, whatever the hour |
| you (a campaign, a reminder, a follow-up) | inside the window |

## The shape of the failure

A messaging system correctly enforces business hours. Someone signs up at
eleven at night and their confirmation is queued until morning.

They were sitting there waiting for it. The window designed to avoid annoying
people produced the single most annoying outcome available: no response to a
deliberate action, at the exact moment attention was highest.

*(Illustrative case.)*

## Why the clock-only rule gets written

Because it is simple, and because the harm it prevents is real and legible —
nobody wants to be the system that messages strangers at midnight. The cost of
over-applying it is invisible: nobody complains about a confirmation that arrived
late, they just leave.

## The implementation

The condition is not the hour. It is a property of the message: **is this a
response to an act by this person, within a short window of that act?** If yes,
send. If no, respect the schedule.

That distinction has to exist in the data — a field on the message saying what
triggered it. If your system cannot tell, the timing rule cannot be correct
either, and that is the real finding.

## The general form

**A protective rule encodes an intention, and the intention is narrower than the
rule.** When the rule and the intention diverge, the rule wins by default because
it is the thing written down. Periodically re-deriving the rule from the
intention is the only way to notice.
