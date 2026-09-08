# Changelog

## 2.0 — 2026-09-08

The project went from three scripts to three parts. What changed, and why.

### Added — the memory got a real engine

- **Ranked retrieval across every project.** BM25 with an inverted index,
  replacing a hand-written keyword map. Measured: 127 ms to 17 ms per prompt,
  which is what returns memory to the 18.7% of prompts that were being discarded
  on time alone.
- **Configuration instead of hardcoded paths.** Everything comes from
  `memory-hooks/config.json`, and every default still works with no config.
- **Layers** — note folders outside the projects tree (a handbook, a vault), with
  a folder allow list and an optional per-layer slot cap, so one large layer
  cannot take every result slot.
- **Long notes are sliced by heading** rather than truncated, so something
  written near the end of a long note is still findable.
- **`/memory-save`** — the command that writes *curated* notes. The automatic
  brief is heuristic; a memory made only of those decays into a log of opening
  sentences.

### Added — `method/`, six gates that refuse

`no_orphan_files`, `destructive_bash`, `project_boundary`, `context_budget`,
`redact_secrets`, and `snapshot`. Opt-in via `install.sh --full`.

Each exists because the corresponding rule had been written down, in a document
that was loaded, and was violated anyway. The clearest case: a note saying
"never through a shell heredoc" was nineteen days old when a nested heredoc
deleted five scripts and five hook registrations.

### Added — `knowledge/`, 56 lessons

Cross-cutting lessons shipped as notes the engine indexes, so they surface on
their own when their subject comes up. The stories are reconstructed; the
lessons are not. See `knowledge/README.md`.

### Added — tests that can fail

- 36 checks on the memory guards, 39 on the gates
- a ranking gate that names which note must return, and how high
- **mutation mode** on both suites: break what each check protects, and fail if
  the check does not notice
- CI on Linux, macOS and Windows, Python 3.8 and 3.12

Seven defects in this release were found by the tests rather than by review,
including a gate that died the first time it tried to refuse anything, and a
backup that returned files 38 bytes larger than it stored them.

### Decided against

**Semantic search.** Built, measured, rejected: a real gain (19 to 23 of 32, no
regressions) that still did not justify replacing a self-contained 114 ms system
with one requiring a local model server — because the problem had been sized by
a purpose-built stress test (81% failure) while the real usage log said 5.8%.
Reopens if the `nohit` rate passes ~15%. Full reasoning in
`engine/docs/MEASUREMENTS.md`.

### Removed

- `install.sh` no longer embeds Python inside a shell heredoc. Editing the
  settings moved to `tools/register_hooks.py`, where it can be read and run on
  its own.

## 1.0 — 2026-04-16

Initial release: three hooks, a keyword map, and Markdown files.
