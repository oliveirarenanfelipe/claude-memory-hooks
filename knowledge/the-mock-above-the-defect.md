---
name: the-mock-above-the-defect
description: A test that injects its dependency ABOVE the point where the bug lives proves nothing about the real path — and its green is more dangerous than no test, because it ends the investigation.
scope: global
type: concept
---

# The mock above the defect

**The rule.** A test that substitutes a dependency **above** the layer where the
bug actually lives never executes the broken code. It passes, honestly, and
proves nothing about the real path.

Its green is worse than having no test at all, because a missing test invites
investigation and a passing test ends it.

## The shape of the failure

A function fetches a record, transforms it and writes it. The bug is in the fetch:
a field arrives in a shape the parser mishandles. The test injects a ready-made
record and asserts on the transform.

Every assertion is correct. The transform is fine. The test cannot see the defect
because the defect lives in the part the test replaced.

*(Illustrative case.)*

## The question that places the mock correctly

> **"Where does the failure I am worried about live, and is my substitution above
> or below it?"**

Mocks belong **below** the thing you are testing, not above the thing you are
worried about. If you are worried about parsing, the parser has to run.

## The stronger version, and it costs one run

**Break the real code and watch this test fail.** If the test stays green while
the code is broken, the mock is above the defect. This is the only check that
does not depend on you correctly guessing where the bug is.

## The organisational tell

When a bug reaches production in code that has good coverage, the first thing to
look at is not the missing test — it is **what the existing tests replaced**.
