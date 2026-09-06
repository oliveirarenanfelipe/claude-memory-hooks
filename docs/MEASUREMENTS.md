# Where the defaults come from

Every number in `hooks/memory_config.py` was measured on a running system, not
picked because it looked reasonable. This file is the record.

**What the measurements were taken on:** one real installation, used daily for
about five months across roughly twenty projects — around 1,600 notes and a log
of several thousand prompts. It is a single corpus, not a benchmark suite. Treat
the numbers as *why this default and not another*, not as a guarantee about your
corpus. Where a number is a target rather than a measurement, it says so.

The point of writing them down is narrower than it looks: without the number, the
next person to touch the code has no way to tell a tuning decision from a
preference, and will "simplify" a value that is holding something up.

---

## Budget — why 1000 ms and not 200

`prompt_memory.py` discards the recall when loading plus searching exceeds
`budget_ms`, so the prompt is never held up.

The first version used 200 ms. Measured over 830 prompts: **155 of them (18.7%)
were discarded — every single one for time, none for lack of a result.** Nearly a
fifth of prompts paid the full cost of the search and received no memory.

The guard is checked *after* load and search have already run. Discarding does
not give any time back; it spends the time and returns nothing, and then makes
the hook run the fallback path on top, which reads more files. A tight budget
made prompts slower *and* memoryless.

1000 ms still protects against the case the guard exists for — a stalled disk, a
corrupt index — and stays 5x below the hook's own 5-second timeout.

**The lesson worth more than the number:** when a guard fires, log *why*. "Slow"
and "found nothing" need opposite fixes, and for months both were logged as the
same string, so there was no way to tell which one was happening.

---

## Inverted index — 127 ms to 17 ms

Measured on a 949-note corpus, comparing the two storage formats:

| | load | search p90 | total |
|---|---|---|---|
| flat cache (token list per note, document frequencies recomputed each search) | 54 ms | 72 ms | **127 ms** |
| inverted index, pickled | 16 ms | 1 ms | **17 ms** |

87% cheaper, a smaller file, and an identical ranking on every regression case.
The gain is not comfort — it is what returns the memory to the 18.7% of prompts
that were being discarded.

Two format choices that are not obvious:

- **Postings are a flat list** `[index, tf, index, tf, ...]`, not a dict or a
  list of tuples. A flat list deserialises far faster. A dict of term frequencies
  measured **100 ms** to load — *worse than the flat cache it replaced* — despite
  occupying fewer bytes.
- **Pickle, not JSON**: 16 ms against 64 ms for the same content. Safe only
  because the file is derived, local, and rebuilt from Markdown whenever it fails
  to load. It is never read from an untrusted source.

---

## Ranking weights

| where the note comes from | multiplier |
|---|---|
| the project you have open | 1.15 |
| marked `scope: global` | 1.10 |
| an extra layer, with no weight of its own | 0.70 |
| another project | 0.50 |

Measured on a log of 2,498 prompts:

- **62.3%** of injected notes came from a project other than the open one
  (7,600 of 12,199);
- of those, only **24.4%** were marked global — the other 5,749 were another
  project's working state, which has no reason to travel;
- in **33.5%** of prompts (837), *none* of the five slots held a note from the
  open project.

The top-k is a fixed number of slots. A neighbour's note does not merely add
noise: it **evicts** the right one. This is also why an earlier attempt at fixing
it did nothing — the open project used to get a 1.15x boost while other projects
paid no penalty at all, and 12.6 × 1.15 = 14.5 does not change a position.

**Multipliers, never filters.** A hard filter would be blind in the case that
actually happens: you are working in project A, you mention something that
genuinely belongs to project B, and B's note is the right answer. At 0.50 it
still wins when it is much more relevant.

**Exclusive, not cumulative.** A note in the open project does not also collect
the global bonus. Stacking them gave the open project 1.265x and silently
invalidated the balance that had been measured.

---

## Note slicing — why long notes are cut by heading

Long notes are sliced by `## ` heading rather than truncated. Measured on the
same corpus:

| index cap | whole notes indexed | of the total body |
|---|---|---|
| 1,500 chars | 18% | 35.8% |
| 5,000 chars | 78% | 75.1% |
| 8,000 chars | 92% | 85.1% |

Raising the cap has a limit that is not about cost. BM25 normalises by document
length (`b = 0.75`), so a long document is *penalised*: indexed whole, a
213,000-character document dropped out of the top-10 even for a term appearing in
it 84 times. Slicing is the only move that makes each part of a long note
reachable on its own terms.

62% of notes in that corpus had headings; 216 were both over 5,000 characters and
sliceable.

---

## Deduplication — counting files, not fragments

Because long notes are sliced, one file can occupy several of the five slots.
Measured across 40 real prompts: **4.65 distinct files per prompt** without
dedup, and — counter-intuitively — penalising other projects made it **worse**
(4.45), because removing competitors let more slices of the same document rise.
With dedup by file: **5.00 of 5**.

The fixture corpus in `tests/` reproduces the failure exactly: on one query, a
single note takes **all five slots** without dedup and four distinct files come
back with it. That case is in the gate.

---

## What is deliberately *not* indexed

- **Session briefs.** `session_context.py` already injects the open project's
  brief in full at session start, so indexing it is redundant for the common
  case. Worse, a brief is short and dense, which BM25 favours: on one query a
  brief took the top slot from the curated note that actually held the answer
  (24.4 against 15.7). Discounts from 0.85 down to 0.30 were tested and **no
  value fixed both sides** — above 0.50 the brief wins, below it disappears even
  when it is the target. A multiplicative discount is the wrong tool; the right
  one, if it is ever needed, is a reserved slot.
- **Auto-generated index pages.** They are built from the descriptions of notes
  that are already indexed, so indexing them duplicates the text and makes the
  map compete with the note it points at.

---

## The staleness guard

The reindex runs on every turn. Rebuilding unconditionally costs most of a second
for nothing, while comparing file count plus newest timestamp costs a few `stat()`
calls.

Two failure modes it is shaped around, both of which happened:

1. **Watching more than the index contains.** Watching a folder that is written
   on every turn — session briefs, an inbox fed by another process — makes the
   timestamp move constantly and the index rebuild forever: 1.8 s per turn
   instead of 120 ms.
2. **Watching without a version number.** Moving files preserves their
   timestamps, so a code change that added a whole new layer left the old index
   in place and the new layer stayed invisible, silently, until someone forced a
   rebuild by hand. `INDEX_VERSION` exists for exactly that.

---

## How to check these on your own corpus

```bash
python tests/golden_recall.py          # ranking + budget, against the fixtures
python tests/golden_recall.py --mutate # break it on purpose; the gate must fail
python tests/test_memory.py            # the guards
```

The budget section prints your real load and search timings and the headroom left
before recall would start being discarded. If the headroom drops below 25%, the
index has grown past what the current budget can carry.

To measure your own recall rather than the fixtures', read `hooks/recall.log`:
each line records the engine, the detected project, the elapsed milliseconds, the
prompt, and which notes were injected — or the reason nothing was.
