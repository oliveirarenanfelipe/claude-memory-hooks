---
name: destructive-writes-must-be-atomic
description: Opening a file for writing truncates it BEFORE anything is written. If the write then fails — an encoding error, a full disk — you are left with zero bytes and the original is gone.
scope: global
type: concept
---

# A destructive write is atomic, or it is not a write

**The rule.** Opening a file in write mode **empties it immediately**, before any
content is produced. If producing the content then fails, the original is gone and
nothing replaced it.

    path.write_text(text, encoding="utf-8")
    #   |- open(path, "w")   -> TRUNCATES here, unconditionally
    #   |- write(text)       -> only now does encoding happen, and fail

Between those two steps there is a window where the old file no longer exists and
the new one does not yet. Any exception in that window leaves **zero bytes**.

## The shape of the failure

A script appends one line to an index file. The content contains a character that
cannot be encoded in the target encoding. The write raises, the traceback is read
as "it did not write" — and the file is empty.

The same applies to `open(path, "w")` written by hand, and to the common idiom of
passing a freshly opened file straight into a serialiser.

The detail that makes it bite twice: the failure looks like a *no-op*. An
exception normally means nothing happened. Here, everything happened except the
part that would have saved you.

*(Illustrative case.)*

## The pattern

Write to a temporary file next to the target, then replace:

    tmp = path + "." + str(os.getpid()) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)          # atomic on the same filesystem

Three properties this buys, all of which matter:

- a failure during writing leaves the original untouched
- the replacement is atomic, so no reader ever sees a half-written file
- the PID in the temp name means two processes cannot promote each other's
  fragments, which matters more than it sounds once anything runs concurrently

## Where it hides

Anywhere a file is rewritten in place rather than appended: config files,
indexes, caches, JSON state, generated output. The risk is proportional to how
much you would mind losing the previous contents — which is exactly why the files
this hits hardest are the important ones.
