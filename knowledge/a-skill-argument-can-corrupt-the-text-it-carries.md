---
name: a-skill-argument-can-corrupt-the-text-it-carries
description: Passing arguments to a template whose body contains positional tokens substitutes those tokens with your words. The document that exists to prevent a stale value delivered a corrupted one.
scope: global
type: concept
---

# An argument can corrupt the text it carries

**The rule.** Any template expanded with positional substitution — `$1`, `%s`,
`{0}` — will substitute those tokens **wherever they appear**, including inside
content that was never meant to be a placeholder.

Pass an argument to a template whose body legitimately contains `$1` and the body
changes.

## The shape of the failure

A reference document contains a price written as `$1,250`. It is invoked with an
argument, and the expansion replaces `$1` with the caller's word. What comes back
is `<word>,250` — a corrupted number, in the document whose entire purpose was to
stop people quoting stale prices from memory.

The output is well formed. Nothing errors. The number is simply different, and it
is exactly the kind of value nobody re-checks because it came from the canonical
source.

*(Illustrative case.)*

## Why this class is so persistent

Because the substitution mechanism cannot distinguish a placeholder from content
that looks like one. It has no notion of intent — only of pattern. Currency, regex,
shell variables, format strings, anything with a sigil is exposed.

## The practice

1. **If the template has no parameters, invoke it with no arguments.** The
   substitution only happens when there is something to substitute.
2. **Escape the sigil in content.** `$$1` in most systems. Tedious and reliable.
3. **Prefer named substitution over positional.** `{price}` collides far less than
   `$1`, and a collision is visible on sight.

## The general form

This is the same family as SQL injection and shell injection, minus an attacker.
**A layer that expands text cannot tell your data from its own syntax** — and when
you are the one who wrote both, the mistake is called an accident instead of a
vulnerability. The mechanism is identical, and so is the fix: keep data out of the
band where syntax is interpreted.
