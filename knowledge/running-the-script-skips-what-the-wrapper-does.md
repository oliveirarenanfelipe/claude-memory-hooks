---
name: running-the-script-skips-what-the-wrapper-does
description: Calling the inner script directly skips everything that lives in the wrapper — the lock, the state commit, the log redirect. The result looks right and the trace is half written.
scope: global
type: concept
---

# Running the script skips what the wrapper does

**The rule.** When a job is a script wrapped by another script, everything that
makes it *safe* usually lives in the wrapper: the lock, the state update, the log
redirect, the notification, the cleanup. Running the inner script directly
produces the right output and **leaves the surroundings half done**.

## The shape of the failure

A pipeline is invoked by a wrapper that takes a lock, runs the work, records
completion and pushes the state. Debugging, someone runs the inner script alone.

It works. The output is correct. But nothing recorded that it ran, so the next
scheduled invocation reprocesses the same items; and no lock was held, so a
concurrent run was possible the whole time.

The failure surfaces later as duplicated work with no apparent cause, because the
run that caused it left no trace — by design, since tracing lived in the wrapper.

*(Illustrative case.)*

## Why "just run the script" is so tempting

Because the wrapper is slow and noisy and you only want the one piece. That is a
legitimate need; the mistake is not noticing you also opted out of five other
things.

## Two fixes, both cheap

1. **Make the inner script refuse to run unwrapped**, unless given an explicit
   flag. One environment variable and three lines.
2. **Make the wrapper thin enough to always run.** If the only reason people skip
   it is that it does too much, move the slow parts behind a flag rather than
   letting people route around the safety.

## The general form

Anywhere the safety lives at a different layer from the work, someone will
eventually invoke the work directly — under time pressure, while debugging. Design
for that moment rather than documenting against it.
