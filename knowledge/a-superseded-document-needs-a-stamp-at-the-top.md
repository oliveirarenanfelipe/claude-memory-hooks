---
name: a-superseded-document-needs-a-stamp-at-the-top
description: A replaced document keeps being used unless it says so in its first lines. People choose by the most obvious name, not the most recent date.
scope: global
type: concept
---

# A superseded document needs a stamp at the top

**The rule.** When a document is replaced, the old one keeps being used unless it
carries a notice **in its first lines**. People do not choose documents by
modification date. They choose by **the most obvious name**, and the obvious name
usually belongs to the old one.

## The shape of the failure

A procedure is revised. The new version is written carefully and lands under a
precise, technical filename. The old one — with the short, memorable name everyone
has bookmarked — is left in place, untouched.

Months later someone executes the old procedure. They were not careless; they
searched, found a document that matched exactly, and it looked current. Nothing
in it said otherwise.

*(Illustrative case.)*

## Why "the new one is right there" does not help

Whoever is about to execute is not surveying the landscape — they are looking for
*the* document, and they stop when they find one that fits. A better version
sitting nearby is invisible to that search.

## The two rules

1. **The notice goes in the first two lines**, not at the end, not in a metadata
   field. Anyone who scrolls past it has already started reading the wrong thing.
2. **The successor inherits the obvious name.** If the old document has the name
   people remember, the new one takes it and the old one is renamed. Precision in
   the successor's filename is worth less than being where people look.

## The minimum stamp

    > SUPERSEDED on <date> by <link>. Do not execute this document.

Three things: that it is dead, what replaced it, and an instruction. The
instruction matters — without it, readers assume the old version is still
"background".

## The general form

This is the documentation instance of a wider pattern: **the artefact that is
easiest to reach wins over the artefact that is correct.** Fixing correctness
without fixing reachability changes nothing.
