---
name: Engineering standards
description: Code review, testing and deploy expectations that apply to every project
---

## Code review
A review looks for correctness first and style last. A reviewer who only comments
on naming has not reviewed the change.

## Testing
Every bug fix arrives with the test that would have caught it. A fix without that
test is a guess that happened to work.

## Deploys
Deploys are reversible or they do not go out on a Friday. Reversible means the
previous version can serve the current database.
