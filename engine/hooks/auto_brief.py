#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_brief.py — Stop hook: write the session brief automatically.

Reads the transcript Claude Code already keeps on disk and extracts the brief
from it. No LLM call, so it costs nothing, needs no API key, and always works.

Two guards that matter more than the extraction itself:
  1. A brief you wrote by hand (`curated: true`) is NEVER overwritten.
  2. When a curated brief is left in place, a dated footer says work happened
     after it — otherwise "curated wins" quietly becomes "curated freezes".

Registered by install.sh as a Stop hook (120s timeout).

Stdlib only. No LLM calls, no API key, no server.
"""
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory_config as cfgmod          # noqa: E402

CODE_EXTS = ('.py', '.js', '.jsx', '.ts', '.tsx', '.json', '.md', '.sh', '.rb',
             '.go', '.rs', '.java', '.sql', '.yml', '.yaml', '.html', '.css', '.toml')

# Messages shorter than this are dropped as noise ("ok", "yes", "thanks"). The
# number is not sacred; it is named so that the code that reports a skipped
# brief can quote it, instead of the person having to guess why nothing happened.
MIN_MESSAGE_CHARS = 16

# Phrases that mark a blocker / a decision / a next step, per language. Override
# with `brief_keywords` in config.json to match how you actually write.
BRIEF_KEYWORDS = {
    "en": {
        "blocker": ["blocked", "waiting on", "waiting for", "not tested yet",
                    "needs approval", "still need to verify", "before we can",
                    "next session", "pending on"],
        "decision": ["decided", "decision", "we chose", "we will use", "going with",
                     "dropped", "not going to use", "replaced by", "renamed to",
                     "architecture", "agreed to"],
        "next": ["next step", "after that", "to continue", "still missing",
                 "still need to", "next session", "remains to"],
    },
    "pt": {
        "blocker": ["bloqueado", "aguardando", "pendente de", "não foi testado",
                    "falta validar", "próxima sessão", "antes de avançar",
                    "precisa de autorização", "falta testar"],
        "decision": ["decidido", "decisão", "optamos por", "vamos usar",
                     "escolhemos", "descartado", "não vai usar", "substituído por",
                     "renomeado para", "arquitetura", "padrão adotado"],
        "next": ["próximo passo", "a seguir", "depois disso", "para continuar",
                 "falta implementar", "pendente", "próxima sessão", "ainda falta"],
    },
}

LABELS = {
    "en": {"date": "Date", "project": "Project", "done": "What was done",
           "files": "Files touched", "decision": "Key decision",
           "next": "Next step", "blocker": "Blocker", "none_f": "None.",
           "none_m": "None.", "fallback": "Work session.",
           "resume": "Continue from", "check": "Review what was done and continue.",
           "warn": "There was work on **{d}** AFTER the last saved brief — "
                   "the summary above may not cover the end of the session."},
    "pt": {"date": "Data", "project": "Projeto", "done": "O que foi feito",
           "files": "Arquivos tocados", "decision": "Decisão importante",
           "next": "Próximo passo", "blocker": "Bloqueio ativo", "none_f": "Nenhuma.",
           "none_m": "Nenhum.", "fallback": "Sessão de trabalho.",
           "resume": "Continuar a partir de", "check": "Verificar o que foi feito e continuar.",
           "warn": "Houve trabalho em **{d}** DEPOIS do último brief salvo — "
                   "o resumo acima pode não cobrir o fim da sessão."},
}


def _lang(cfg):
    langs = cfg.get("language") or "en"
    if isinstance(langs, list):
        langs = langs[0] if langs else "en"
    return str(langs).lower() if str(langs).lower() in LABELS else "en"


def _keywords(cfg, lang):
    base = BRIEF_KEYWORDS.get(lang, BRIEF_KEYWORDS["en"])
    return {**base, **(cfg.get("brief_keywords") or {})}


def read_transcript(path: str) -> list:
    """The JSONL transcript as [{role, text}] — tool traffic dropped."""
    messages = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    role = d.get("message", {}).get("role", "")
                    if role not in ("user", "assistant"):
                        continue
                    content = d["message"].get("content", "")
                    text = ""
                    if isinstance(content, list):
                        for c in content:
                            if isinstance(c, dict) and c.get("type") == "text":
                                text = c.get("text", "")
                                break
                    elif isinstance(content, str):
                        text = content
                    text = text.strip()
                    if (text and len(text) >= MIN_MESSAGE_CHARS
                            and not text.startswith("<tool_result")):
                        messages.append({"role": role, "text": text})
                except Exception:
                    pass
    except Exception:
        pass
    return messages


def extract_files(messages: list) -> list:
    pattern = re.compile(r'[`\s]([A-Za-z0-9_/\\.-]+\.[a-zA-Z]{1,5})\b')
    files = set()
    for m in messages:
        for match in pattern.findall(m["text"]):
            if match.lower().endswith(CODE_EXTS):
                files.add(match)
    return sorted(files)[:8]


def _sentence_with(messages, keywords, fallback, window=None, min_len=15, cap=300):
    pool = messages[-window:] if window else messages
    for m in reversed(pool):
        low = m["text"].lower()
        for kw in keywords:
            if kw in low:
                for sentence in m["text"].split("."):
                    if kw in sentence.lower() and len(sentence.strip()) >= min_len:
                        return sentence.strip()[:cap]
    return fallback


def first_sentence(text: str, max_chars: int = 200) -> str:
    text = text.replace("\n", " ").strip()
    for sep in (". ", "! ", "? "):
        idx = text.find(sep)
        if 0 < idx < max_chars:
            return text[:idx + 1].strip()
    return text[:max_chars].strip()


def extract_what_done(messages: list, labels: dict) -> str:
    user = [m for m in messages if m["role"] == "user"]
    assistant = [m for m in messages if m["role"] == "assistant"]
    lines = []
    for m in user:
        if len(m["text"]) > 30:
            lines.append(first_sentence(m["text"], 220))
            break
    if assistant:
        paragraphs = [p.strip() for p in assistant[-1]["text"].split("\n\n")
                      if len(p.strip()) > 30]
        if paragraphs:
            lines.append(paragraphs[0][:300].replace("\n", " "))
    return " — ".join(lines)[:600] if lines else labels["fallback"]


def extract_next_step(messages: list, kw: dict, labels: dict) -> str:
    assistant = [m for m in messages if m["role"] == "assistant"]
    found = _sentence_with(assistant, kw["next"], None, window=4)
    if found:
        return found
    user = [m for m in messages if m["role"] == "user"]
    if user:
        return f"{labels['resume']}: {user[-1]['text'][:150]}"
    return labels["check"]


def generate_brief(messages, slug, cfg) -> str:
    lang = _lang(cfg)
    labels = LABELS[lang]
    kw = _keywords(cfg, lang)
    files = extract_files(messages)
    files_line = (f"\n**{labels['files']}:** "
                  + ", ".join(f"`{f}`" for f in files)) if files else ""
    return (
        f"**{labels['date']}:** {datetime.now().strftime('%Y-%m-%d')}\n"
        f"**{labels['project']}:** {slug}\n\n"
        f"**{labels['done']}:** {extract_what_done(messages, labels)}\n"
        f"{files_line}\n\n"
        f"**{labels['decision']}:** "
        f"{_sentence_with(messages, kw['decision'], labels['none_f'], min_len=20)}\n\n"
        f"**{labels['next']}:** {extract_next_step(messages, kw, labels)}\n\n"
        f"**{labels['blocker']}:** "
        f"{_sentence_with(messages, kw['blocker'], labels['none_m'], window=6, cap=200)}"
    )


def is_curated(path: Path) -> bool:
    """True when the brief was written by hand rather than by this hook.

    The earlier version of this check also required the brief to carry the id of
    the session in progress. The intention was good — an old brief should still
    be refreshable — but the condition was impossible to satisfy: whoever writes
    a curated brief has no access to that id, so the only source was the file
    itself, which holds the PREVIOUS session's id until this hook runs. Deriving
    the id from the file you are about to overwrite is circular, and the result
    was that hand-written briefs were destroyed on every single session.
    """
    try:
        return "curated: true" in path.read_text(encoding="utf-8", errors="replace")[:600]
    except Exception:
        return False


def mark_unsaved_session(path: Path, labels: dict) -> None:
    """Append one dated line: there was a session after the curated brief.

    Idempotent per DAY. This hook runs on every turn, not once at the end, so
    appending per call would fill the file within a single session — and stamping
    "ended without saving" moments after a save would simply be false. If the
    curated brief is already from today there is nothing to warn about, and a
    stale marker from a previous day is removed rather than stacked.
    """
    mark = "<!-- unsaved-session:"
    today = datetime.now().strftime("%Y-%m-%d")
    line = (f"\n{mark} {today} -->\n"
            f"> ⚠️ {labels['warn'].format(d=today)}\n")
    try:
        txt = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return
    if f":** {today}" in txt[:900]:
        if mark in txt:
            path.write_text(txt[:txt.find(mark)].rstrip() + "\n", encoding="utf-8")
        return
    cut = txt.find(mark)
    if cut != -1:
        txt = txt[:cut].rstrip() + "\n"
    try:
        path.write_text(txt.rstrip() + "\n" + line, encoding="utf-8")
    except Exception:
        pass


def save_brief(path: Path, slug: str, content: str, session_id: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = (f"---\n"
                   f"name: Brief — {slug}\n"
                   f"description: Last session of project {slug}\n"
                   f"type: project\n"
                   f"originSessionId: {session_id}\n"
                   f"---\n")
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(frontmatter + content, encoding="utf-8")
    os.replace(tmp, path)


def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except Exception:
        sys.exit(0)

    transcript = data.get("transcript_path") or data.get("transcriptPath", "")
    cwd = data.get("cwd", "")
    session_id = data.get("session_id") or data.get("sessionId", "unknown")
    quiet = json.dumps({"continue": True, "suppressOutput": True})

    if not transcript or not os.path.exists(transcript):
        print(quiet)
        sys.exit(0)

    messages = read_transcript(transcript)
    # A session with too little in it does not produce a useful brief. But the
    # threshold used to be silent, and silence here is indistinguishable from
    # "it worked" — someone who answers "ok", "yes", "do it" can close a real
    # session and get no brief at all, with nothing said. Caught in testing: a
    # four-message conversation produced nothing because one reply was six
    # characters long and fell under the length filter in read_transcript.
    #
    # So: still no brief, and now it SAYS so. The message costs one line and
    # turns an invisible gap into a fact the person can act on.
    user_messages = [m for m in messages if m["role"] == "user"]
    if len(user_messages) < 2:
        print(json.dumps({
            "continue": True, "suppressOutput": True,
            "systemMessage": ("No brief written — this session had %d substantial "
                              "message(s) from you and needs 2. Short replies "
                              "(under %d characters) do not count."
                              % (len(user_messages), MIN_MESSAGE_CHARS))}))
        sys.exit(0)

    cfg = cfgmod.load()
    slug = cfgmod.detect_project(cwd, cfg) or "session"
    path = cfgmod.briefs_dir_for(cwd) / f"{slug}.md"

    if path.exists() and is_curated(path):
        mark_unsaved_session(path, LABELS[_lang(cfg)])
        print(quiet)
        sys.exit(0)

    save_brief(path, slug, generate_brief(messages, slug, cfg), session_id)
    print(json.dumps({"continue": True, "suppressOutput": True,
                      "systemMessage": f"📝 Brief saved — {slug}"}))


if __name__ == "__main__":
    main()
