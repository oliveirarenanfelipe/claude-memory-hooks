---
name: the-container-lies-about-the-contents
description: Duration, file size, byte counts and loudness measure the CONTAINER. To prove something about the contents, count the contents — three green checks passed while a third of the files were missing their audio.
scope: global
type: concept
---

# The container lies about the contents

**The rule.** File size, duration, exit code, HTTP status and row count all
describe the **container**. None of them says anything about what is inside it.
If your claim is about the contents, the check has to count the contents.

## The shape of the failure

A pipeline produces fifteen video files. Three checks guard it:

1. every file exists — green
2. every file is the expected duration — green
3. every file reports a loudness within range — green

Six of the fifteen have **no audio track at all**. Each check was true. The files
existed; a file with a silent track still has a duration; and a missing track
reports a loudness value like any other absent signal does.

Three green checks, and a third of the output was broken.

*(Illustrative case; the shape is the point.)*

## Why it is so common

Container properties are cheap to read and always available. Content properties
require knowing what the content is supposed to be. So the easy check gets
written first, passes, and nobody writes the second one — the suite is green,
and green ends the conversation.

## The question that separates them

> **"Would this check still pass if the file were empty in exactly the way I am
> worried about?"**

If yes, you are measuring the container.

## The pattern in other clothes

| the container says | what it does not say |
|---|---|
| HTTP 200 | the body is not an empty list |
| exit code 0 | the command did the work rather than skipping it |
| the file is 4 MB | the 4 MB are the right 4 MB |
| the table has 1,200 rows | the rows are this week's |
| the build succeeded | the build included your change |

The last one has a specific trap worth naming: a stale build artefact makes a
tool compare a version of the code with **itself**, and every difference
disappears. Green, and meaningless.
