# Security

This project reads your notes, writes files under your Claude directory, and — at
the `--full` level — inspects shell commands and rewrites tool output. That is a
lot of access, so here is exactly what it does with it.

## What it touches

| | |
|---|---|
| **reads** | notes under your projects' `memory/` folders, plus any folders you list as `layers` in your config |
| **writes** | session briefs, a search index, and a log of why each prompt got the memory it got |
| **sends** | **nothing.** No network calls, no telemetry, no API keys, no accounts |

There is no server component and no service to sign up for. Disconnect the
machine from the internet and everything here still works.

## What it deliberately refuses to do

- **The snapshot never commits a secret.** Before saving your memory directory to
  git it scans what would be committed and aborts on anything matching a
  credential pattern, naming the file in `gates.log`.
- **The `redact_secrets` gate rewrites credential-shaped values out of tool
  results** before they reach the conversation, so a token returned by a
  third-party tool does not end up in a stored transcript.
- **The ignore list is an allow list.** `method/memory-dir.gitignore` starts by
  ignoring everything and permits only what has been reviewed, so a file nobody
  anticipated is excluded by default rather than included by default.

## Known limits, stated rather than implied

- **Redaction matches known credential shapes.** A secret that looks like
  ordinary prose — a password inside a sentence, an internal hostname that is
  itself sensitive — passes through. This narrows the opening; it does not close
  it.
- **Creating the snapshot repository is a decision.** The installer offers it and
  declines by default. Review `git status` yourself before the first snapshot:
  the automatic scan is a second line of defence, not the first.
- **A layer configured as `recursive` indexes whatever is in that folder.** Prefer
  the `folders` allow list. A recursive sweep over a folder nobody curated will
  pull in whatever happens to be sitting there.

## Reporting something

Open an issue. If it is a vulnerability rather than a bug, describe the class of
problem rather than a working exploit, and say what an attacker would gain.

This is a personal project with no service behind it, so there is no bounty and
no guaranteed response window — but a security issue goes to the front of the
queue.
