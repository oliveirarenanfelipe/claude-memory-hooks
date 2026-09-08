#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
redact_secrets.py — PostToolUse: no secret enters the conversation, from anywhere.

Why this exists
---------------
A tool returned, inside a SUCCESSFUL response, a pagination URL with a full
access token in its query string. Measured that week: **15 occurrences of the
token in plain text across the session transcripts**. The token did not expire
and could spend money.

The important part is where it came from. Nobody printed it, nobody logged it,
no code was careless. A third-party tool put it in a normal, correct response —
and from there it went into the transcript, which is stored, indexed, and later
read back as memory.

Filtering the one tool that leaked was rejected as a fix, and rightly:

    "it will keep leaking the same way it leaked today, so the only solution is
     to treat it so that it does not leak anywhere."

So this runs on the output of EVERY tool, and it does not care which one.

What it does
------------
Scans the tool result for credential patterns and replaces each match with
`[REDACTED: <kind>]`. The conversation keeps the shape of the data — you can
still see there was a token, and where — without the value.

Two behaviours that are not obvious and both matter:

**It never blocks.** A redaction hook that refused a tool result would break the
work on a false positive. It rewrites and continues.

**It reports what it redacted.** Silent redaction is its own trap: a value
disappearing from a file you wrote yourself reads as a bug in the file. Knowing
the redactor touched something is what stops an hour spent debugging a defect
that does not exist.

Known limitation, stated rather than hidden: this catches values matching KNOWN
credential shapes. A secret that looks like ordinary text — a password inside a
sentence, an internal URL that is itself sensitive — passes through. This narrows
the opening; it does not close it.

Registered by install.sh as a PostToolUse hook.
Stdlib only.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_lib as gl  # noqa: E402

GATE = "redact_secrets"

# Ordered most specific first: a JWT also matches some generic patterns, and the
# label in the redaction should say the most useful thing.
PATTERNS = [
    (re.compile(r"ghp_[A-Za-z0-9]{30,}"), "GitHub token"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{30,}"), "GitHub token"),
    (re.compile(r"gh[opsu]_[A-Za-z0-9]{30,}"), "GitHub token"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "Slack token"),
    (re.compile(r"AIza[0-9A-Za-z_-]{30,}"), "Google API key"),
    (re.compile(r"sk-(?:proj-|ant-)?[A-Za-z0-9_-]{25,}"), "API key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
     "private key"),
    (re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}"), "JWT"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key"),
    # In a URL query string — how the leak that produced this hook actually
    # happened. The value stops at the first separator, so the rest of the URL
    # (often the useful part) survives.
    (re.compile(r"(?i)([?&](?:access_token|api_key|apikey|token|key|secret|password|"
                r"auth|signature|sig)=)[^&\s\"'<>]{8,}"), "token in URL"),
    # An assignment with a long literal value.
    (re.compile(r"(?i)\b((?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|"
                r"password|passwd|secret)\s*[:=]\s*[\"']?)([^\s\"',;]{16,})"),
     "credential assignment"),
]

MAX_SCAN = 2_000_000       # do not scan enormous payloads: cost without benefit


def redact(text):
    """(text_with_redactions, [kinds]) — never raises."""
    if not text or len(text) > MAX_SCAN:
        return text, []
    kinds = []
    for pattern, kind in PATTERNS:
        def _sub(match, kind=kind):
            kinds.append(kind)
            # Keep the leading group (the `?token=` or the `api_key = `) when the
            # pattern captured one, so the reader still sees WHERE it was.
            if match.groups():
                return match.group(1) + "[REDACTED: %s]" % kind
            return "[REDACTED: %s]" % kind
        text = pattern.sub(_sub, text)
    return text, kinds


def handle(event):
    result = event.get("tool_response")
    if result is None:
        result = event.get("tool_result")
    if result is None:
        return

    was_string = isinstance(result, str)
    original = result if was_string else json.dumps(result, ensure_ascii=False)
    cleaned, kinds = redact(original)
    if not kinds:
        return

    counts = {}
    for kind in kinds:
        counts[kind] = counts.get(kind, 0) + 1
    summary = ", ".join("%d %s" % (n, k) for k, n in sorted(counts.items()))
    gl.log(GATE, "redact", gl.tool_name(event), summary)

    gl.stdout_utf8()
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                "A tool result contained credential-shaped values, and they were "
                "replaced with [REDACTED] markers before reaching this "
                "conversation (%s). If a value looks missing from a file you "
                "wrote yourself, suspect this hook before suspecting the file."
                % summary)},
        "modifiedToolResponse": cleaned,
    }, ensure_ascii=False))


if __name__ == "__main__":
    gl.run(GATE, handle)
