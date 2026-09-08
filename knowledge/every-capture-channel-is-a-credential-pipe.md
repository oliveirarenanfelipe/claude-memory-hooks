---
name: every-capture-channel-is-a-credential-pipe
description: Any channel where people forward things — a chat bot, a shared inbox, a clipping tool — is an ingestion pipe for OTHER people's credentials. A forwarded link carries tokens in its query string.
scope: global
type: concept
---

# Every capture channel is a credential pipe

**The rule.** Any channel where people send things in — a capture bot, a shared
inbox, a bookmarking tool, a paste box — is also an **ingestion pipe for
credentials that are not yours**. Not because anyone intends it: because a
forwarded link carries whatever was in its query string.

## The shape of the failure

A capture channel stores whatever is sent to it. Someone forwards a link to a
document from a service that authenticates by URL parameter. The stored record now
contains a working access token for a third party's account.

It is not in an obvious field, nobody typed it, and standard secret scanners do
not look inside URLs in stored text. It sits in the archive indefinitely, and it
gets included in every backup and every index built from that archive.

*(Illustrative case.)*

## Why the usual defences miss it

Secret scanning looks for credential **shapes** — key prefixes, private key
headers — in source files. A signed URL matches none of those patterns and lives
in a data store, not in code. Every layer behaves correctly and the token passes
through all of them.

## The practice

1. **Strip query strings on ingestion**, keeping only what you need. If the link
   must be preserved whole, store it in a field marked as sensitive.
2. **Scan the capture store, not just the repository.** The pipe deposits into a
   place nobody thought to point a scanner at.
3. **Treat the archive as containing third-party secrets**, and set retention
   accordingly. The exposure is not yours to accept on someone else's behalf.

## The general form

**Anywhere content crosses a trust boundary inbound, it carries more than the
sender intended.** Uploaded documents carry metadata and revision history; images
carry location; forwarded links carry authentication. The sender did not choose to
send those things, which is exactly why nobody looks for them.
