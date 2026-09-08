---
name: the-check-that-passes-for-the-wrong-reason
description: A green check proves nothing until you have seen it fail. Break the thing on purpose: if the check stays green, it was never watching what you think it was.
scope: global
type: concept
---

# The check that passes for the wrong reason

**The rule.** A check that has only ever passed is not evidence. Before trusting
it, **break the thing it guards on purpose and watch it fail**. If it stays
green, it was never watching what you think it was watching.

## Three ways a check goes green while guarding nothing

**1. It is disarmed and still runs.** A guard is looked up by a keyword that the
code no longer produces, or by a path that moved. The check executes, finds
nothing to object to, and reports success. Absence of a finding is
indistinguishable from absence of a problem.

**2. It is true by accident.** The assertion holds for a reason unrelated to what
it claims. A test asserts `len(results) > 0` and passes because the fallback path
returned something — while the ranking it was written to protect is destroyed.

**3. It cannot fire in time.** The check is correct but slower than the timeout of
whatever calls it. That produces no error, no alarm and no log line: it produces
**absence**, which reads exactly like "passed". A gate that decides correctly and
decides too late is a gate that is switched off, silently.

*(Illustrative shapes; each one is a failure mode, not a story.)*

## The practice

**Mutation.** Take the thing the check protects and break it deliberately:

- invert the weights the ranking depends on
- delete the data source the check reads
- empty the list of patterns it matches against
- remove the fix and confirm the original symptom returns

Then assert that the check **reports failure**. Automate this next to the check
itself, so it runs whenever the check runs. A mutation you only performed once,
by hand, decays into a story about the past.

## Why this is not paranoia

Every one of the three failures above is invisible from the outside. The suite
looks the same when it is working and when it is not — same green, same duration,
same output. Mutation is the only cheap thing that distinguishes them.

The corollary is uncomfortable and worth saying plainly: **a suite that has never
gone red is not a suite that never found a bug. It is a suite you have no reason
to believe.**
