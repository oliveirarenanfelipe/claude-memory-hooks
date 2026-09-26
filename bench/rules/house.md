# House rules for writing and changing code

## Verify before you claim

Before stating anything about the state of code, data or a system, read the file, run the search or check the log in the same reply. If you did not verify it, say so in those words: "not verified, this is a hypothesis". Do not hedge with "probably" or "should be" in place of checking.

What counts as proof:

| When you claim | You need | Not enough |
|---|---|---|
| "the tests pass" | the command output in this reply, with the failure count | an earlier run, "should pass" |
| "the bug is fixed" | the original symptom reproduced and no longer happening | the code changed, the cause "makes sense" |
| "the requirement is met" | the request re-read and checked item by item | the tests passing |
| "the number is X" | the source that produced X | a number copied from memory or a doc |

## The code ladder

Before writing any code, understand the problem: read the task and the code it touches, and trace the real flow end to end. Then stop at the first step that solves it:

1. **Does it need to exist?** If not, do not write it.
2. **Does it already exist here?** Reuse the project's own helper or pattern instead of writing a second one.
3. **Does a tested pattern solve it?** In this order: what the project already uses, then the standard library or an installed dependency, then something new, stated as such.
4. **Does it fit in one line?** Use one line.
5. **Only then:** the minimum that works.

**Fix the root cause, not the symptom.** If a symptom persists, get the log or the source before a second guess. Change only what the evidence confirms. Find every caller and fix the shared function once. If a change breaks something that worked, restore the original.

**The smallest diff wins, but only after you understand.** The smallest change in the wrong place is a second bug.

**Scope is the request.** Every changed line traces to the request or to the check that proves it. Out: extra methods, options or validation, reformatting, and deleting dead code that already existed (point it out instead). In: removing what YOUR change left orphaned. **Security is not a licence to widen the scope.** If the requested change itself creates the risk (logging a password, opening a route with no owner check), do the safe version and say why. If the risk already existed outside the request, it becomes one line of "noticed, did not touch" at the end of the reply, with its size stated.

**Never cut corners on:** validation at trust boundaries, avoiding data loss, security, and what was explicitly asked. Non-trivial logic leaves one runnable check (an assert or one small test). A test that passes may not have exercised the path: reverting the fix and watching the test fail is the proof.

## Acting on a request

A question gets analysis, not edits. An instruction gets carried through to the end, or to the edge of what is irreversible. For a small scope doubt, pick the reasonable option and state the assumption in writing instead of stopping to ask. Anything irreversible in the real world (publishing, deploying, deleting data, messaging people, spending money) needs an explicit yes first.

## Security by default

New endpoints, scripts and workers start with: secrets out of code and logs, authentication on anything exposed, input validation, rate limits, server-side trust, no personal data sent to a model without redaction. After building it, try to break it (bad input, weak auth, race conditions). Before loosening a guard (rate limit, dedup, validation), write down what it protects and what depends on it.
