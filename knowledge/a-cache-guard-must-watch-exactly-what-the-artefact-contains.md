---
name: a-cache-guard-must-watch-exactly-what-the-artefact-contains
description: A 'does this need rebuilding?' check must watch exactly the set the artefact holds. Watch more and it rebuilds forever; watch less and it serves stale output, silently.
scope: global
type: concept
---

# A cache guard must watch exactly what the artefact contains

**The rule.** Every "do I need to rebuild?" check watches a set of inputs. That
set must match **exactly** what the artefact was built from. Both errors are
silent and they fail in opposite directions.

| | consequence |
|---|---|
| **watching MORE** than the artefact contains | rebuilds constantly, for changes that could not affect it — expensive, and blamed on the wrong thing |
| **watching LESS** | serves a stale artefact indefinitely, and nothing reports it |

## The two shapes

**Watching more.** A rebuild guard watches a whole directory, including a file
that another process rewrites every few seconds. The guard now fires on every
check. What was meant to cost a few file stats costs a full rebuild each time,
and the symptom — "everything is slow" — points nowhere near the cause.

**Watching less.** A new source of input is added to the build. The guard is not
updated. The artefact is now built from five things and validated against four,
so a change in the fifth never triggers anything. It stays invisible until
someone forces a rebuild by hand and the output changes for no apparent reason.

*(Illustrative cases.)*

## The third failure, which is nastier

**A structural change with no version marker.** When the *shape* of the artefact
changes — a new field, a new section — the old artefact remains valid by every
check the guard performs. Counts match, timestamps match. The new capability
simply never appears.

Moving files preserves their timestamps, so even a large reorganisation can leave
every guard satisfied.

The fix is a **version stamped inside the artefact**, compared on load. It costs
one integer and it is the only thing that catches this class.

## The practice

Write the guard and the builder **next to each other**, reading the same list of
inputs from the same place. When they are separate, they drift, and the drift is
undetectable from either side.
