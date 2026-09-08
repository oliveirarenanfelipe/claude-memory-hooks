---
name: the-text-you-write-can-be-executed
description: Content you are generating is DATA, and a shell can turn it into COMMANDS. A nested heredoc reusing the same delimiter closes the outer one, and the rest of your text runs.
scope: global
type: concept
---

# The text you write can be executed

**The rule.** When you generate a script as *content* — text destined for a file —
the boundary between data and command is held by whatever you pass it through. A
shell holds that boundary badly, and when it slips, your draft runs.

## The shape of the failure

A script is being written. Its content is passed to an interpreter through a shell
heredoc:

    python - <<'BLOCK'
    content = '''#!/usr/bin/env bash
    ...
    "$PY" - <<'BLOCK'          # <-- the same delimiter, inside the content
    ...
    BLOCK
    '''
    write(content)
    BLOCK

The inner `BLOCK` **closes the outer one**. From that line onward the shell stops
treating the text as content and starts executing it — including the lines that
resolve paths against a real home directory and delete files.

Result: six script files deleted, five configuration entries stripped, an index
and a log gone. All of it from text that was never meant to run.

*(Illustrative reconstruction of a real class of accident.)*

## Why "be careful with heredocs" does not hold

Because the rule addresses attention, and the failure is structural. The nesting
is invisible at a glance — the delimiters look balanced, the quoting looks right,
and the whole thing is usually one line in a much larger command.

A rule stating exactly this had been written down nineteen days earlier, in those
words, by the same person who then made the mistake.

## The practice

1. **Content that itself contains shell or code goes through a file-writing tool,
   never through a shell heredoc.** A write tool treats its payload as data by
   construction; a shell cannot tell the difference.
2. If it must be a heredoc, **never nest, and never reuse a delimiter**.
3. **Make it a gate, not a note.** A check that inspects the command before it
   runs and refuses a nested heredoc costs a few lines and does not depend on
   anyone remembering.

## The general form

Any time you build a program that builds a program, ask which layer is quoting
what. Shell, SQL, HTML, YAML, regex, a templating language — the class is the
same, and it is called injection when an attacker does it and an accident when
you do it to yourself. The mechanism is identical.
