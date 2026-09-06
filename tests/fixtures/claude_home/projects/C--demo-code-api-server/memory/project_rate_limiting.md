---
name: Rate limiting at the edge
description: Token bucket per API key, and why the limit lives at the edge and not in the app
type: project
---

Rate limiting runs in the edge worker, not in the application. A limiter inside
the app still pays for connection setup and a database round trip before it says
no, so an abusive client costs almost as much when blocked as when served.

## The bucket
Token bucket, 100 requests per minute per API key, burst of 20. Counters live in
the edge key-value store with a 60 second expiry.

## What we got wrong first
The first version keyed the bucket on client IP. Every customer behind a single
office NAT shared one bucket and throttled each other. Keying on the API key
fixed it; IP is only used for unauthenticated endpoints.
