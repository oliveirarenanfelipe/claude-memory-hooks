#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
golden_recall.py — the regression gate for recall quality.

    python tests/golden_recall.py            # run the gate
    python tests/golden_recall.py -v         # show the top-3 of every case
    python tests/golden_recall.py --mutate   # prove the gate can actually FAIL

Why this file exists
--------------------
A unit test that asserts `len(results) > 0` passes while the ranking is
destroyed. Without a gate that names WHICH note must come back and HOW HIGH,
every change to the index is faith. This is the ruler.

Why --mutate exists
-------------------
A gate that has only ever passed is not evidence. `--mutate` deliberately breaks
the thing each case is supposed to protect and asserts that the gate REPROVES.
A gate that stays green under mutation is decoration, and it will stay green
through a real regression too.

Reads only the synthetic corpus in tests/fixtures — never your own notes.
Exit code: 0 = every regression case passed · 1 = a regression · 2 = broken setup.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fixture_env as fx                # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

API, WEB, NOTES = fx.API, fx.WEB, fx.NOTES

# (question, cwd, file that MUST come back, worst acceptable position)
# Baselines measured against the fixture corpus, not assumed. Each case protects
# a specific behaviour, named in the comment — a case whose purpose you cannot
# name is a case you cannot maintain.
REGRESSION = [
    # the ordinary job: the right note of the open project, first
    ("how do refresh tokens get rotated", API, "project_auth_tokens.md", 1),
    ("why is the rate limit keyed on the api key and not the ip", API,
     "project_rate_limiting.md", 1),
    ("can we drop a column in the same release", API, "project_db_migrations.md", 1),
    ("where do customers abandon the checkout", WEB, "project_checkout_flow.md", 1),
    ("dark mode colour tokens", WEB, "project_design_system.md", 1),
    ("why do we reject backend candidates", NOTES, "note_hiring_loop.md", 1),

    # an extra LAYER (a handbook, a shared folder) is reachable from any project
    ("who runs the incident and what does the commander do", API,
     "incident_response.md", 1),
    ("does every bug fix need a test", WEB, "engineering_standards.md", 1),

    # a note marked `scope: global` crosses project boundaries; without that,
    # every cross-cutting lesson is trapped in the project it was written in
    ("should I change quality without measuring it", API,
     "concept_measure_before_fixing.md", 1),

    # DEEP BODY: both terms below live past character 7000 of a 7.5k note. With a
    # truncating index they are unreachable; only slicing by heading finds them.
    ("what is the cardinality budget for labels", API, "project_observability.md", 1),
    ("do we sample traces at the head or the tail", API, "project_observability.md", 1),
]

# Cases that fail today and are the goal of the next step. They do not fail the
# build; when one starts passing, the gate says so and tells you to promote it —
# otherwise the improvement is not protected and can silently regress.
PENDING = []

# A query matching several slices of ONE long note. Measured on this corpus:
# without dedup that single file takes ALL FIVE slots and the other four answers
# never reach the prompt; with dedup, four distinct files come back.
# The check below also verifies that the query still triggers the risk — a dedup
# case that no longer matches multiple slices passes for the wrong reason and
# stops protecting anything.
DEDUP_CASE = ("the rule we settled on for metrics and dashboards and reviews and tests", API)

# The same note, scored from its own project and from a neighbour. Proves the
# ranking actually knows where you are standing.
HOME_BOOST_CASE = ("validation rules", "project_form_validation.md", WEB, API)


def position(ml, idx, query, cwd, target, top_k=10):
    project = ml.detect_project(cwd)
    hits = ml.bm25_search_idx(query, idx, project, top_k=top_k)
    for i, (score, n) in enumerate(hits, 1):
        if Path(n["file"]).name == target:
            return i, score, hits
    return None, None, hits


def run_gate(ml, idx, verbose=False, quiet=False, cfg=None):
    """Returns the list of failures. Empty list = approved."""
    failures = []

    def say(*a):
        if not quiet:
            print(*a)

    say("== REGRESSION (must always pass) ==")
    for q, cwd, target, worst in REGRESSION:
        pos, _score, hits = position(ml, idx, q, cwd, target)
        ok = pos is not None and pos <= worst
        if not ok:
            failures.append((q, target, worst, pos))
        where = f"#{pos}" if pos else "outside top-10"
        say(f"  [{'PASS' if ok else 'FAIL'}] {q[:52]:<52} -> {where} (max #{worst})")
        if verbose or (not ok and not quiet):
            for i, (s, n) in enumerate(hits[:3], 1):
                say(f"           {i}. {Path(n['file']).name} ({n['project']}, {s:.1f})")

    say("\n== DEDUP (one note must not eat every slot) ==")
    q, cwd = DEDUP_CASE
    project = ml.detect_project(cwd)
    # The undeduped ranking, to prove the risk is actually present. Without this
    # the case can pass because nothing matched twice — approval for the wrong
    # reason, and the protection silently stops existing.
    keep = ml._top_k_distinct
    try:
        ml._top_k_distinct = lambda out, k: out[:k]
        raw = [Path(n["file"]).name for _s, n in
               ml.bm25_search_idx(q, idx, project, top_k=5)]
    finally:
        ml._top_k_distinct = keep
    hits = ml.bm25_search_idx(q, idx, project, top_k=5)
    files = [Path(n["file"]).name for _s, n in hits]

    risk = len(raw) - len(set(raw))               # repeats the dedup must remove
    distinct = len(files) == len(set(files))
    enough = len(files) >= 2
    ok = risk >= 1 and distinct and enough
    if not ok:
        why = ("query no longer matches one file twice" if risk < 1
               else "duplicate files in the result" if not distinct
               else "fewer than 2 results")
        failures.append((q, f"dedup ({why})", 0, len(set(files))))
    say(f"  [{'PASS' if ok else 'FAIL'}] undeduped: {len(set(raw))} distinct of "
        f"{len(raw)} slots -> deduped: {len(set(files))} distinct of {len(files)}")

    say("\n== HOME BOOST (the ranking knows which project you are in) ==")
    q, target, home_cwd, away_cwd = HOME_BOOST_CASE
    _p1, home, _h1 = position(ml, idx, q, home_cwd, target)
    _p2, away, _h2 = position(ml, idx, q, away_cwd, target)
    ok = home is not None and away is not None and home > away
    if not ok:
        failures.append((q, f"{target} scoring higher at home", 0, None))
    say(f"  [{'PASS' if ok else 'FAIL'}] {target}: "
        f"{'-' if home is None else round(home, 1)} at home vs "
        f"{'-' if away is None else round(away, 1)} away")

    if PENDING:
        say("\n== PENDING (fails today; this is the goal) ==")
        promoted = []
        for q, cwd, target, worst in PENDING:
            pos, _s, _h = position(ml, idx, q, cwd, target)
            ok = pos is not None and pos <= worst
            if ok:
                promoted.append((q, target, pos))
            say(f"  [{'NOW PASSES' if ok else 'pending'}] {q[:52]:<52} "
                f"-> {f'#{pos}' if pos else 'absent'}")
        if promoted and not quiet:
            print(f"\n*** {len(promoted)} pending case(s) now pass. Move them to "
                  f"REGRESSION, or the improvement is not protected. ***")

    return failures


def run_budget(ml, cfgmod, quiet=False):
    """The guard that stops anyone 'improving' the index by making it too slow.

    prompt_memory.py DISCARDS the recall when load+search exceeds budget_ms. A
    change that pushes the p90 past the budget makes recall worse with no error
    anywhere in the log — the memory simply stops arriving.
    """
    budget = float(cfgmod.load().get("budget_ms", 1000))
    t0 = time.perf_counter()
    idx = ml.load_index()
    load_ms = (time.perf_counter() - t0) * 1000

    times = []
    for q, cwd, _t, _w in REGRESSION:
        project = ml.detect_project(cwd)
        t1 = time.perf_counter()
        ml.bm25_search_idx(q, idx, project, top_k=5)
        times.append((time.perf_counter() - t1) * 1000)
    times.sort()
    p50 = times[len(times) // 2]
    p90 = times[max(0, int(len(times) * 0.9) - 1)]
    total = load_ms + p90
    headroom = (1 - total / budget) * 100

    if not quiet:
        print(f"\n== BUDGET (discard threshold: {budget:.0f} ms, read from config) ==")
        print(f"  load index:        {load_ms:7.1f} ms")
        print(f"  search p50 / p90:  {p50:7.1f} / {p90:.1f} ms")
        print(f"  TOTAL p90:         {total:7.1f} ms   (headroom {headroom:+.0f}%)")
    if total > budget:
        if not quiet:
            print("  *** OVER BUDGET — recall would be DISCARDED with this config ***")
        return [("[budget]", f"p90 {total:.0f}ms", budget, None)]
    if headroom < 25 and not quiet:
        print("  NOTE: under 25% headroom — little room for the index to grow")
    return []


# ---------------------------------------------------------------------------
# mutation: break it on purpose and demand that the gate notices
# ---------------------------------------------------------------------------
MUTATIONS = [
    ("neighbours outrank the open project",
     "Notes from other projects score 10x. If the gate stays green, it is not "
     "protecting the project boundary at all.",
     {"weights": {"current_project": 1.0, "global_scope": 1.0,
                  "other_project": 10.0, "default_layer": 10.0}}),
    ("extra layers removed",
     "The handbook layer disappears. The gate must notice that a whole source "
     "of answers went missing.",
     {"layers": []}),
    ("long notes truncated instead of sliced",
     "Slicing is switched off and notes are cut at 1500 characters — the state "
     "this project came from. Anything written late in a long note becomes "
     "unreachable.",
     {"note_cap": 1500, "chunk_min": 10 ** 9}),
]


def run_mutations():
    print("== MUTATION (break it on purpose; the gate must REPROVE) ==\n")
    survived = []
    for name, why, overrides in MUTATIONS:
        cfgmod, ml = fx.setup(**overrides)
        fx.fresh_index(ml)
        idx = ml.load_index()
        failures = run_gate(ml, idx, quiet=True, cfg=cfgmod)
        caught = len(failures) > 0
        print(f"  [{'CAUGHT' if caught else 'SURVIVED'}] {name}")
        print(f"           {why}")
        print(f"           gate reported {len(failures)} failure(s)")
        if not caught:
            survived.append(name)
        print()

    # restore the real fixture config, so a later run is not poisoned by a mutation
    cfgmod, ml = fx.setup()
    fx.fresh_index(ml)

    if survived:
        print(f"REPROVED — {len(survived)} mutation(s) went undetected. The gate "
              f"does not protect what it claims to:")
        for name in survived:
            print(f"   {name}")
        return 1
    print(f"APPROVED — all {len(MUTATIONS)} mutations were caught.")
    return 0


def main():
    verbose = "-v" in sys.argv
    if "--mutate" in sys.argv:
        return run_mutations()

    cfgmod, ml = fx.setup()
    fx.fresh_index(ml)
    idx = ml.load_index()
    if not idx:
        print("BROKEN: no index was built. Check tests/fixtures/.")
        return 2

    projects = len(list(ml.iter_memory_dirs()))
    print(f"GOLDEN RECALL — fixture corpus — {idx['N']} indexed unit(s) from "
          f"{projects} project(s) plus configured layers\n")

    failures = run_gate(ml, idx, verbose=verbose, cfg=cfgmod)
    failures += run_budget(ml, cfgmod)

    print()
    if failures:
        print(f"REPROVED — {len(failures)} regression(s):")
        for q, target, worst, got in failures:
            print(f"   {q!r} expected {target} by #{worst}, got "
                  f"{got if got else 'nothing'}")
        return 1
    print(f"APPROVED — {len(REGRESSION)} regression case(s), plus dedup, home "
          f"boost and budget.")
    print("Now run `python tests/golden_recall.py --mutate` — a gate that has "
          "only ever passed is not evidence.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
