"""Measure whether a rules file changes how Claude Code writes code.

Every reply runs in an isolated `claude -p --restricted --strict-mcp-config --tools ""`
from an empty folder: no CLAUDE.md, no hooks, no memory, no MCP servers. The rules
under test enter through --append-system-prompt-file, one arm per file in rules/,
plus an arm with no rules at all. A blind judge (same isolation) sees every reply to
a case, shuffled and unlabeled, and counts violations against that case's rubric.

    python bench.py answer            # generate replies  (arms x cases x reps)
    python bench.py judge             # one blind judge per case
    python bench.py score             # print the table

Options: --cases cases.json  --reps 2  --run runs/default  --arms none,house,karpathy
Replies already on disk are reused, so an interrupted run resumes.
"""
import argparse, io, json, random, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).parent

PROMPT = (
    "You are a coding assistant helping a user in a Python project (Flask + SQLAlchemy unless the code "
    "says otherwise). There is no repository beyond the code shown. You cannot run anything. "
    "Write exactly the reply you would give the user in this turn (text and/or code/diff) and nothing else.\n\n"
    "User message: \"{request}\"\n\n{code}"
)

JUDGE = (
    "You are a blind judge. Do not use tools. Below are {n} replies (labeled {labels}) from coding assistants "
    "to the SAME user request. Count each reply's violations against the rubric, strictly, without rewarding "
    "length or politeness. A violation counts once per code.\n\n"
    "USER REQUEST: \"{request}\"\n\n{code}\n\nEVALUATOR NOTE (the replies did not see this): {note}\n\n"
    "RUBRIC:\n{rubric}\n- V0: handed the decision back without proposing any concrete minimal path.\n\n{replies}\n\n"
    "OUTPUT ONLY a JSON object, no prose, in this shape: "
    "{{\"A\": {{\"v\": [\"V1\"], \"n\": 1, \"why\": \"short\"}}, ...}} with one key per label."
)

ISOLATED = ["claude", "-p", "--restricted", "--strict-mcp-config"]


def claude(extra, prompt, dest, empty_dir):
    if dest.exists() and dest.stat().st_size > 50:
        return "reused"
    r = subprocess.run(ISOLATED + extra + ["--tools", ""], input=prompt, capture_output=True,
                       text=True, encoding="utf-8", cwd=empty_dir, timeout=600)
    dest.write_text(r.stdout, encoding="utf-8")
    return r.returncode


def setup(a):
    run = Path(a.run)
    (run / "replies").mkdir(parents=True, exist_ok=True)
    empty = run / "_empty"
    empty.mkdir(exist_ok=True)
    cases = json.loads(Path(a.cases).read_text(encoding="utf-8"))
    return run, empty, cases


def answer(a):
    run, empty, cases = setup(a)
    jobs = []
    for c in cases:
        prompt = PROMPT.format(request=c["request"], code=c.get("code", ""))
        for arm in a.arms:
            extra = [] if arm == "none" else ["--append-system-prompt-file", str(HERE / "rules" / f"{arm}.md")]
            for rep in range(1, a.reps + 1):
                jobs.append((extra, prompt, run / "replies" / f"{c['id']}_{arm}_{rep}.md", empty))
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(lambda j: claude(*j), jobs))
    print("replies:", len(res), "status:", sorted(set(map(str, res))))


def judge(a):
    run, empty, cases = setup(a)
    rnd = random.Random(20260925)
    key, jobs = {}, []
    for c in cases:
        items = [f"{arm}_{rep}" for arm in a.arms for rep in range(1, a.reps + 1)]
        rnd.shuffle(items)
        labels = [chr(65 + i) for i in range(len(items))]
        key[c["id"]] = dict(zip(labels, items))
        blocks = [f"=== REPLY {l} ===\n" + (run / "replies" / f"{c['id']}_{it}.md").read_text(encoding="utf-8").strip()
                  for l, it in zip(labels, items)]
        p = JUDGE.format(n=len(items), labels=", ".join(labels), request=c["request"], code=c.get("code", ""),
                         note=c["note"], rubric=c["rubric"], replies="\n\n".join(blocks))
        jobs.append(([], p, run / f"judge_{c['id']}.json", empty))
    (run / "judge_key.json").write_text(json.dumps(key, indent=1), encoding="utf-8")
    with ThreadPoolExecutor(4) as ex:
        print("judges:", list(ex.map(lambda j: claude(*j), jobs)))


def score(a):
    run = Path(a.run)
    key = json.loads((run / "judge_key.json").read_text(encoding="utf-8"))
    total = {arm: 0 for arm in a.arms}
    print("case | " + " | ".join(a.arms))
    for cid, labels in key.items():
        raw = (run / f"judge_{cid}.json").read_text(encoding="utf-8")
        verdict = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
        per = {arm: [] for arm in a.arms}
        for label, item in labels.items():
            arm = item.rsplit("_", 1)[0]
            n = int(verdict[label]["n"])
            per[arm].append(n)
            total[arm] += n
        print(cid, "|", " | ".join("+".join(map(str, per[arm])) for arm in a.arms))
    print("TOTAL |", " | ".join(str(total[arm]) for arm in a.arms))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["answer", "judge", "score"])
    ap.add_argument("--cases", default=str(HERE / "cases.json"))
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--run", default=str(HERE / "runs" / "default"))
    ap.add_argument("--arms", default="none,house,karpathy", type=lambda s: s.split(","))
    a = ap.parse_args()
    {"answer": answer, "judge": judge, "score": score}[a.step](a)
