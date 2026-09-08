#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_gates.py — proves the gates refuse, allow, and can actually fail.

    python method/gates/tests/test_gates.py

Three parts, and the third is the one that matters:

  1. MUST REFUSE — including the exact command that deleted five hook scripts.
  2. MUST ALLOW — including the ordinary patterns people use every day. A gate
     that blocks the right work becomes a tax, and taxes get uninstalled. This
     half of the suite is not politeness; it is what keeps the gates installed.
  3. MUTATION — each detector is disarmed and the behaviour must CHANGE. A guard
     that still works with its detector switched off is not the thing doing the
     guarding.

Nothing here touches your real directories: every gate runs as a subprocess with
a synthetic payload, and the snapshot test builds a throwaway git repository in a
temp folder.

No pytest, no dependencies.
Exit code: 0 = everything passed and every mutation was caught.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

TESTS = os.path.dirname(os.path.abspath(__file__))
GATES = os.path.dirname(TESTS)
sys.path.insert(0, GATES)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PASSED = FAILED = 0
survived = []


def check(name, ok, extra=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print("  PASS  " + name)
    else:
        FAILED += 1
        print("  FAIL  " + name + ("   " + extra if extra else ""))


def run_gate(script, payload, env=None):
    """Runs a gate the way Claude Code does: JSON on stdin, JSON on stdout."""
    process = subprocess.run(
        [sys.executable, os.path.join(GATES, script)],
        input=json.dumps(payload).encode("utf-8"),
        capture_output=True, timeout=60, env=env)
    out = process.stdout.decode("utf-8", "replace").strip()
    if not out:
        return None
    try:
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"]
    except Exception:
        return "INVALID OUTPUT: " + out[:100]


def bash(command):
    return {"tool_name": "Bash", "tool_input": {"command": command}}


# A fresh session id per RUN. The "interrupt once per session" marker lives in a
# temp file that outlives the process, so a fixed id makes the second run of this
# suite pass for the wrong reason: the gate correctly stays quiet because it
# already spoke, and the test reads that as the gate being broken.
RUN_ID = "test-%d-%d" % (os.getpid(), int(__import__("time").time()))


def write(path):
    return {"tool_name": "Write", "tool_input": {"file_path": path},
            "session_id": RUN_ID + "-" + os.path.basename(path)}


# The accident, reconstructed: the inner PYEOF closes the outer one.
THE_ACCIDENT = (
    "cd /repo && python - <<'PYEOF'\n"
    "from pathlib import Path\n"
    "install = r'''#!/usr/bin/env bash\n"
    'CLAUDE_DIR="${CLAUDE_HOME:-$HOME/.claude}"\n'
    "\"$PY\" - <<'PYEOF'\n"
    "import os\n"
    "from pathlib import Path\n"
    "claude = Path(os.environ['CLAUDE_DIR'])\n"
    "for s in scripts:\n"
    "    (claude / 'hooks' / s).unlink()\n"
    "PYEOF\n"
    "'''\n"
    "Path('install.sh').write_text(install)\n"
    "PYEOF"
)

# A nested heredoc that touches nothing protected. Exists to ISOLATE the heredoc
# detector: the accident above trips both rules at once, so disarming one of them
# would not free it — and a mutation that cannot isolate proves nothing.
NESTED_ONLY = (
    "python - <<'BLOCK'\n"
    'text = """\n'
    "cat > f.sh <<'BLOCK'\n"
    "echo hi\n"
    "BLOCK\n"
    '"""\n'
    "print(text)\n"
    "BLOCK"
)

print("== destructive_bash: MUST REFUSE ==")
for name, command in [
    ("the exact accident (nested heredoc)", THE_ACCIDENT),
    ("nested heredoc alone, touching nothing", NESTED_ONLY),
    ("rm on a hook", 'rm -f "$HOME/.claude/hooks/prompt_memory.py"'),
    ("cp overwriting a hook", "cp backup/x.py ~/.claude/hooks/x.py"),
    ("python deleting inside it",
     "python -c \"import shutil;shutil.rmtree('~/.claude/projects')\""),
    ("redirect over the settings", 'echo "{}" > ~/.claude/settings.json'),
    ("git reset --hard with options in between",
     "git -C ~/.claude reset --hard origin/main"),
]:
    check(name, run_gate("destructive_bash.py", bash(command)) == "deny")

print("\n== destructive_bash: MUST ALLOW (or the gate becomes a tax) ==")
for name, command in [
    ("plain reading", "cat ~/.claude/hooks/memory_lib.py | head -40"),
    ("grep", 'grep -rn "budget" ~/.claude/hooks/'),
    ("running a script from there", "python ~/.claude/hooks/reindex_memory.py"),
    ("two SEQUENTIAL heredocs sharing a name",
     "cat > a.md <<'E'\nfirst\nE\ncat > b.md <<'E'\nsecond\nE"),
    ("nested heredocs with DIFFERENT delimiters",
     "python - <<'OUTER'\nprint('ok')\n# inside: cat <<'INNER'\nOUTER"),
    ("destructive OUTSIDE the protected path", "rm -rf /tmp/scratch/build"),
    ("destructive WITH the deliberate marker",
     "cp backup/x.py ~/.claude/hooks/x.py  # GATE-OK: restoring after the incident"),
]:
    check(name, run_gate("destructive_bash.py", bash(command)) is None)

print("\n== no_orphan_files ==")
# The suite must give the same result wherever the repository happens to sit.
# It did not: run from a checkout inside the system temp directory, every case
# here failed, because `temp` is one of the default exemptions and the whole
# tree was therefore exempt. The test was reading its own location as a verdict.
# So it declares its own exemption list instead of inheriting the environment's.
tmp = os.path.join(TESTS, "_workspace")
shutil.rmtree(tmp, ignore_errors=True)
os.makedirs(tmp, exist_ok=True)
try:
    home = os.path.join(tmp, "home")
    os.makedirs(os.path.join(home, ".claude", "memory-hooks"), exist_ok=True)
    with open(os.path.join(home, ".claude", "memory-hooks", "config.json"),
              "w", encoding="utf-8") as fh:
        json.dump({"gates": {"no_orphan_files": {
            "extensions": [".py"],
            "ignore": ["scratch", "node_modules"],
            "search_roots": [tmp]}}}, fh)
    env = dict(os.environ)
    env["HOME"] = home
    env["USERPROFILE"] = home

    check("a new code file is interrupted once",
          run_gate("no_orphan_files.py",
                   write(os.path.join(tmp, "helper_service.py")), env) == "deny")
    existing = os.path.join(tmp, "already_here.py")
    open(existing, "w").close()
    check("an existing file is not a new piece",
          run_gate("no_orphan_files.py", write(existing), env) is None)
    check("a note is not code",
          run_gate("no_orphan_files.py",
                   write(os.path.join(tmp, "notes.md")), env) is None)
    scratch = os.path.join(tmp, "scratch", "throwaway.py")
    os.makedirs(os.path.dirname(scratch), exist_ok=True)
    check("an exempt directory is exempt",
          run_gate("no_orphan_files.py", write(scratch), env) is None)

    # The exemption must match a whole path SEGMENT, never a substring. This case
    # exists because the suite failed exactly here when run from a checkout
    # living under a folder named "scratchpad": the word "scratch" matched inside
    # it and the gate was silently off for that entire tree.
    lookalike = os.path.join(tmp, "scratchpad_project", "service.py")
    os.makedirs(os.path.dirname(lookalike), exist_ok=True)
    check("a folder merely CONTAINING an exempt word is still gated",
          run_gate("no_orphan_files.py", write(lookalike), env) == "deny")
    nested = os.path.join(tmp, "app", "node_modules_backup", "x.py")
    os.makedirs(os.path.dirname(nested), exist_ok=True)
    check("'node_modules_backup' is not 'node_modules'",
          run_gate("no_orphan_files.py", write(nested), env) == "deny")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("\n== context_budget ==")
tmp = tempfile.mkdtemp(prefix="gates_")
try:
    watched = os.path.join(tmp, "INSTRUCTIONS.md")
    with open(watched, "w", encoding="utf-8") as fh:
        fh.write("# rules\n\n## Open items\n\n- short line\n")
    cfg_dir = os.path.join(tmp, "home", ".claude", "memory-hooks")
    os.makedirs(cfg_dir, exist_ok=True)
    with open(os.path.join(cfg_dir, "config.json"), "w", encoding="utf-8") as fh:
        json.dump({"gates": {"context_budget": {"files": [
            {"path": watched, "max_kb": 1, "index_sections": ["## Open items"],
             "max_line_chars": 60, "detail_goes_to": "the project notes"}]}}}, fh)

    env = dict(os.environ)
    env["HOME"] = os.path.join(tmp, "home")
    env["USERPROFILE"] = os.path.join(tmp, "home")

    big = {"tool_name": "Write", "session_id": RUN_ID + "-b1",
           "tool_input": {"file_path": watched, "content": "x" * 3000}}
    check("an edit over the size budget is refused",
          run_gate("context_budget.py", big, env) == "deny")

    long_line = {"tool_name": "Write", "session_id": RUN_ID + "-b2",
                 "tool_input": {"file_path": watched,
                                "content": "## Open items\n\n- " + "y" * 200 + "\n"}}
    check("a too-long line inside a declared index is refused",
          run_gate("context_budget.py", long_line, env) == "deny")

    fine = {"tool_name": "Write", "session_id": RUN_ID + "-b3",
            "tool_input": {"file_path": watched,
                           "content": "## Open items\n\n- still short\n"}}
    check("an edit within budget goes through",
          run_gate("context_budget.py", fine, env) is None)

    other = {"tool_name": "Write", "session_id": RUN_ID + "-b4",
             "tool_input": {"file_path": os.path.join(tmp, "other.md"),
                            "content": "z" * 5000}}
    check("a file that is not watched is left alone",
          run_gate("context_budget.py", other, env) is None)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("\n== redact_secrets: no secret enters the conversation ==")


def run_redact(tool_response):
    payload = {"tool_name": "Bash", "tool_response": tool_response}
    process = subprocess.run(
        [sys.executable, os.path.join(GATES, "redact_secrets.py")],
        input=json.dumps(payload).encode("utf-8"), capture_output=True, timeout=60)
    out = process.stdout.decode("utf-8", "replace").strip()
    if not out:
        return None
    return json.loads(out).get("modifiedToolResponse")


TOKEN = "ghp_" + "A" * 36
# The leak that produced this hook: a token inside a URL, in a SUCCESSFUL result.
LEAK_URL = "https://api.example.com/v1/items?limit=50&access_token=" + TOKEN + "&after=xyz"
cleaned = run_redact(LEAK_URL)
check("a token in a URL is redacted",
      cleaned is not None and TOKEN not in cleaned, str(cleaned)[:80])
check("and the rest of the URL survives",
      cleaned is not None and "api.example.com" in cleaned and "after=xyz" in cleaned,
      str(cleaned)[:100])
check("and it still shows WHERE the value was",
      cleaned is not None and "access_token=" in cleaned, str(cleaned)[:100])
check("a bare token is redacted",
      TOKEN not in str(run_redact("here is the token " + TOKEN + " use it")))
JWT = "eyJhbGciOiJIUzI1NiJ9." + "b" * 40 + "." + "c" * 20
check("a JWT is redacted", JWT not in str(run_redact("Authorization: Bearer " + JWT)))
check("a private key block is redacted",
      "MIIEvQ" not in str(run_redact(
          "-----BEGIN RSA PRIVATE KEY-----\nMIIEvQIBADANBg\n-----END RSA PRIVATE KEY-----")))
check("ordinary output is left completely alone",
      run_redact("ok: 12 files changed, 340 insertions(+)") is None)
check("a short phrase that merely says 'key' is not touched",
      run_redact("the key is in the drawer") is None)

_denied = subprocess.run([sys.executable, os.path.join(GATES, "redact_secrets.py")],
                         input=json.dumps({"tool_name": "Bash",
                                           "tool_response": TOKEN}).encode(),
                         capture_output=True, timeout=60)
check("it rewrites and NEVER denies",
      b'"permissionDecision"' not in _denied.stdout and _denied.returncode == 0)

print("\n== CLAUDE_HOME is honoured (a sandboxed run must stay sandboxed) ==")
import gate_lib as gl_check      # noqa: E402
import snapshot as snap          # noqa: E402
import destructive_bash as db    # noqa: E402
import redact_secrets as rs      # noqa: E402

# This case exists because the opposite happened: an end-to-end test pointed at
# a throwaway directory and the snapshot resolved to the REAL one anyway. It did
# not commit, only because an unrelated interval had not elapsed. A test that
# believes it is sandboxed and is not is worse than no test.
_sandbox = os.path.join(tempfile.gettempdir(), "gates_home_check")
os.makedirs(_sandbox, exist_ok=True)
_previous_home = os.environ.get("CLAUDE_HOME")
os.environ["CLAUDE_HOME"] = _sandbox
try:
    check("claude_home() follows CLAUDE_HOME",
          gl_check.claude_home() == _sandbox, gl_check.claude_home())
    check("the gate log follows it too",
          gl_check.log_path().startswith(_sandbox), gl_check.log_path())
    check("the snapshot target follows it too",
          snap.config()[0] == _sandbox, snap.config()[0])
finally:
    if _previous_home is None:
        os.environ.pop("CLAUDE_HOME", None)
    else:
        os.environ["CLAUDE_HOME"] = _previous_home
    shutil.rmtree(_sandbox, ignore_errors=True)

print("\n== snapshot: saves, and REFUSES to save a secret ==")


def new_repo():
    d = tempfile.mkdtemp(prefix="gates_repo_")
    subprocess.run(["git", "-C", d, "init", "-q"], check=True)
    subprocess.run(["git", "-C", d, "config", "user.name", "t"], check=True)
    subprocess.run(["git", "-C", d, "config", "user.email", "t@t"], check=True)
    os.makedirs(os.path.join(d, "hooks"), exist_ok=True)
    with open(os.path.join(d, "hooks", "x.py"), "w") as fh:
        fh.write("print(1)\n")
    subprocess.run(["git", "-C", d, "add", "-A"], check=True)
    subprocess.run(["git", "-C", d, "commit", "-q", "-m", "init"], check=True)
    return d


def commits(d):
    r = subprocess.run(["git", "-C", d, "rev-list", "--count", "HEAD"],
                       capture_output=True, text=True)
    return int(r.stdout.strip() or 0)


repos = []
try:
    repo = new_repo(); repos.append(repo)
    snap.config = lambda: (repo, 20, ("hooks/",))
    before = commits(repo)
    snap.take_snapshot()
    check("no change -> nothing is committed", commits(repo) == before)

    with open(os.path.join(repo, "hooks", "x.py"), "w") as fh:
        fh.write("print(2)\n")
    before = commits(repo)
    snap.take_snapshot()
    check("a STRUCTURAL change is committed immediately",
          commits(repo) == before + 1, "commits=%d" % commits(repo))

    repo2 = new_repo(); repos.append(repo2)
    snap.config = lambda: (repo2, 20, ("hooks/",))
    with open(os.path.join(repo2, "hooks", "leak.py"), "w") as fh:
        fh.write("TOKEN = 'ghp_" + "A" * 36 + "'\n")
    before = commits(repo2)
    snap.take_snapshot()
    check("a secret in the change -> ABORTS without committing",
          commits(repo2) == before, "commits=%d" % commits(repo2))

    print("\n== MUTATION ==")

    repo3 = new_repo(); repos.append(repo3)
    snap.config = lambda: (repo3, 20, ("hooks/",))
    with open(os.path.join(repo3, "hooks", "leak.py"), "w") as fh:
        fh.write("TOKEN = 'ghp_" + "B" * 36 + "'\n")
    before = commits(repo3)
    keep = snap.SECRET_PATTERNS
    snap.SECRET_PATTERNS = []
    try:
        snap.take_snapshot()
    finally:
        snap.SECRET_PATTERNS = keep
    changed = commits(repo3) == before + 1
    print("  [%s] snapshot: secret detector disarmed"
          % ("CAUGHT" if changed else "SURVIVED"))
    print("           With the list empty the secret MUST get committed. If it")
    print("           does not, something else was blocking and the guard is fake.")
    if not changed:
        survived.append("snapshot secret detector")

    keep_heredoc = db.nested_same_delimiter
    db.nested_same_delimiter = lambda _c: None
    try:
        still = bool(db.analyse(NESTED_ONLY))
    finally:
        db.nested_same_delimiter = keep_heredoc
    print("  [%s] destructive_bash: nested-heredoc detector disarmed"
          % ("CAUGHT" if not still else "SURVIVED"))
    print("           The isolated nested heredoc must stop being flagged.")
    if still:
        survived.append("nested heredoc detector")

    keep_verbs = db.DESTRUCTIVE
    db.DESTRUCTIVE = []
    try:
        still = bool(db.analyse("rm -rf ~/.claude/hooks"))
    finally:
        db.DESTRUCTIVE = keep_verbs
    print("  [%s] destructive_bash: verb list emptied"
          % ("CAUGHT" if not still else "SURVIVED"))
    print("           With no verbs, a destructive command must stop being flagged.")
    if still:
        survived.append("destructive verb list")

    keep_patterns = rs.PATTERNS
    rs.PATTERNS = []
    try:
        text_after, kinds = rs.redact("token " + TOKEN)
    finally:
        rs.PATTERNS = keep_patterns
    caught = TOKEN in text_after and not kinds
    print("  [%s] redact_secrets: pattern list emptied"
          % ("CAUGHT" if caught else "SURVIVED"))
    print("           With no patterns the token MUST come through untouched. If")
    print("           it is still redacted, something else is doing the work.")
    if not caught:
        survived.append("redact_secrets pattern list")
finally:
    for d in repos:
        shutil.rmtree(d, ignore_errors=True)

print("\n=== RESULT: %d passed / %d failed / %d mutation(s) survived ==="
      % (PASSED, FAILED, len(survived)))
for s in survived:
    print("   undetected mutation: " + s)
sys.exit(1 if (FAILED or survived) else 0)
