---
name: Auth tokens and refresh rotation
description: How access and refresh tokens are issued, stored and rotated in the API
type: project
---

Access tokens are short lived (15 minutes) and signed with RS256. The refresh
token lives in an httpOnly cookie and is rotated on every use: presenting an
already-used refresh token revokes the whole family, which is what catches a
stolen cookie being replayed from a second machine.

## Why rotation and not a long-lived token
A long-lived bearer token cannot be revoked without a denylist, and a denylist is
a second source of truth about who is logged in. Rotation keeps one source.

## Clock skew
Token validation allows 30 seconds of skew. Below that, users behind a badly
synchronised corporate proxy were rejected at random.
