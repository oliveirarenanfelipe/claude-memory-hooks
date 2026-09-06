---
name: Zero downtime database migrations
description: Expand and contract migration pattern, and the rule about dropping columns
type: project
---

Every schema change is expand-then-contract. Add the new column, backfill it,
start writing to both, switch reads, and only then drop the old one, in a
separate release, never the same one.

## The rule about dropping
A column is never dropped in the release that stops using it. The rollback of
that release would then hit a database that no longer has the column, which turns
a bad deploy into an outage.
