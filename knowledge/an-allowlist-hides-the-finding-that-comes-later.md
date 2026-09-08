---
name: an-allowlist-hides-the-finding-that-comes-later
description: Silencing a scanner by PATH silences the whole class in that path, including the real finding that appears there tomorrow. And an audit run from inside the repo inherits the repo's blind spots.
scope: global
type: concept
---

# An allowlist hides the finding that comes later

**The rule.** Suppressing a scanner by **path** does not suppress one known
false positive. It suppresses **the entire class, in that location, forever** —
including the genuine finding that appears there next month.

## The shape of the failure

A secret scanner flags a test fixture containing a fake credential. The obvious
fix is to add the file, or its folder, to the ignore list. The scan goes green
and stays green.

Later, an audit run from **outside** the repository, with its own configuration,
reports findings in files the internal scan had been calling clean for months.

Both scans were working correctly. They disagreed because one of them was reading
the suppression list of the thing it was auditing.

*(Illustrative case.)*

## The second half, which is worse

**An audit that runs inside the audited repository inherits its blind spots.** It
reads the same ignore file, the same config, the same exclusions — so it can only
find what the repository was already willing to look for. It reports green with
complete sincerity.

This is not a hypothetical property of scanners; it is true of any check that
takes its configuration from the thing being checked. Linters, test selection,
coverage exclusions, dependency audits.

## The practice

1. **Suppress the finding, not the path.** Most tools support ignoring a specific
   match by its fingerprint. That expires naturally when the content changes,
   which is exactly the behaviour you want.
2. **Where only path suppression exists, make the path as narrow as the fixture** —
   one file, never a folder, never a glob.
3. **A green scan is only meaningful next to its ignore list.** Reporting "clean"
   without saying what was excluded is reporting a number without its units.
4. **Run one audit from outside, with its own config**, periodically. It is the
   only version that can see what the inside version was told not to.

## The tell

If you cannot say, from memory, what your scanner is currently ignoring, its
green result is not information.
