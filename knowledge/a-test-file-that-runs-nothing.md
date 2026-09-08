---
name: a-test-file-that-runs-nothing
description: A file named like a test, containing no test, is collected by the runner and executes zero assertions. The suite closes green and the gate never ran at all.
scope: global
type: concept
---

# A test file that runs nothing

**The rule.** Test runners discover by naming convention. A file called
`test_something.py` that contains no function matching the convention is
collected, contributes zero tests, and **removes nothing from the green result**.

## The shape of the failure

Three baseline checks guarding production output are written as scripts: they
compute, they print, they compare. They live in files named like tests. The
suite has passed every day for weeks.

None of them ever ran an assertion. The runner opened each file, found nothing to
call, and moved on. Every deploy went out with three guards that existed only as
files.

*(Illustrative case.)*

## Why nothing complains

Zero collected tests is not an error condition for any runner — it is the normal
state of a file that legitimately has no tests. The count of executed tests
appears in the output, and nobody reads a number that has always been there.

## The cheap detector

**Compare the number of test FILES with the number of test CASES executed.** If a
file contributes zero, that is a defect, not a preference. Most runners can fail
on zero collected; turn it on.

And once, by hand: break an assertion on purpose and confirm the suite goes red.
If it stays green, that check was never running.

## The general form

Any mechanism that discovers work by pattern will silently skip what does not
match: test collection, plugin loading, migration discovery, hook registration,
cron file naming. **Discovery failures are always silent, because from the
discoverer's side nothing happened.**
