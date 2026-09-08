#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
question_is_analysis.py — when the message was a QUESTION, the answer is analysis,
not execution.

The problem
-----------
You think out loud. You ask whether something might work, or wonder if an
approach is wrong, or say "we should probably look at X". The assistant starts
editing files.

Nothing was authorised. The message was a question, and questions are how people
think — but an eager assistant reads every message as an instruction, because
almost all of them are. So the rare one that is not gets executed too.

The cost is not the wasted work. It is that you stop thinking out loud, because
thinking out loud has consequences. That is a real loss and it happens quietly.

This one is worth a gate specifically because writing it down does not work. In
the setup this came from, the rule existed in the always-loaded instruction file
and was still violated roughly twenty times in five weeks — often enough that the
person had to keep typing "don't execute" by hand.

What this does
--------------
When the last thing you said looks like a question or a reflection, the FIRST
write or command in that turn is refused once. The assistant has to say what it
understood and confirm before acting. Reading, searching and analysing are never
blocked — those are exactly what a question deserves.

Say "do it", "go ahead", "fix it" and nothing is blocked at all: an explicit
instruction switches the gate off for that turn.

Why once, and why only the first action
---------------------------------------
Because the goal is a moment of confirmation, not an obstacle course. One
interruption costs a sentence; interrupting every action would make the gate a
tax, and taxes get uninstalled — after which they protect nothing. Answer, get
the go-ahead, and the rest of the turn runs normally.

Configure in `~/.claude/memory-hooks/config.json`:

    "gates": {
      "question_is_analysis": {
        "language": ["en", "pt"],
        "extra_question_markers": ["what if", "i wonder"],
        "extra_command_markers": ["ship it", "just do it"]
      }
    }

Registered by install.sh as a PreToolUse hook (matcher: Edit|Write|Bash).
Stdlib only.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_lib as gl  # noqa: E402

GATE = "question_is_analysis"

# An explicit instruction. Checked FIRST: if the person told you to act, nothing
# below matters. Being generous here is what keeps the gate from being a tax.
COMMAND_MARKERS = {
    "en": ["do it", "go ahead", "please do", "fix it", "fix this", "implement",
           "apply it", "apply that", "make it", "build it", "write it", "run it",
           "add it", "remove it", "delete it", "update it", "change it",
           "go for it", "you can do", "can you do it", "let's do", "lets do",
           "proceed", "ship it", "execute", "carry on", "continue", "attack",
           # Bare imperatives. Safe next to the reflection openers, which are
           # checked first: "should we remove X?" stays a question because the
           # opener frames it. Deliberately NOT included: words that commonly
           # appear in plain descriptions of what happened — "deploy", "break",
           # "fail" — which would turn a status report into an instruction.
           "add", "rename", "remove", "delete", "update", "create", "refactor",
           "replace", "revert", "rewrite", "extract", "rename it"],
    "pt": ["faz", "faça", "pode fazer", "pode atacar", "ataca",
           "executa", "execute", "implementa", "implemente", "aplica", "aplique",
           "corrige", "corrija", "arruma", "arrume", "roda", "rode", "escreve",
           "escreva", "cria", "crie", "adiciona", "adicione", "acrescenta",
           "acrescente", "atualiza", "atualize", "remove", "remova", "apaga",
           "apague", "troca", "troque", "move", "mova", "renomeia", "renomeie",
           "pode seguir", "segue", "siga", "manda", "pode ir", "resolve",
           "resolva", "finaliza", "finalize", "termina", "termine"],
}

# Reflection markers: the message is thinking, not instructing.
QUESTION_MARKERS = {
    "en": ["what do you think", "do you think", "should we", "should i",
           "could we", "could it", "is it worth", "does it make sense",
           "makes sense", "wondering", "i wonder", "not sure", "am i right",
           "is that right", "what would", "how would", "why does", "why is",
           "is there", "are there", "any idea", "thoughts on", "your opinion"],
    "pt": ["o que voce acha", "o que você acha", "o que acha", "sera que",
           "será que", "vale a pena", "faz sentido", "sera melhor",
           "será melhor", "estou pensando", "to pensando", "tô pensando",
           "qual a sua", "qual sua", "poderia ser", "seria melhor",
           "porque nao", "por que nao", "por que não", "tem como", "da para",
           "dá para", "voce acha", "você acha", "alguma ideia", "sugestao",
           "sugestão", "o que voce me diz", "o que você me diz"],
}

# Openings that make the whole sentence a question, even when it contains a verb
# of action further along. "Is it worth DOING this" is a question about doing it,
# not an instruction to do it — and without this the action verb wins and the
# gate stays quiet on exactly the message it exists for.
REFLECTION_OPENERS = {
    "en": ["is it worth", "does it make sense", "do you think", "what do you think",
           "should we", "should i", "would it be better", "wouldn't it be better",
           "any reason to", "is there a reason"],
    "pt": ["sera que", "será que", "vale a pena", "faz sentido", "voce acha",
           "você acha", "o que acha", "nao seria melhor", "não seria melhor",
           "seria melhor", "tem sentido", "faria sentido"],
}

ACTION_TOOLS = ("Edit", "Write", "NotebookEdit", "Bash")


def config():
    cfg = gl.gate_config(GATE)
    langs = cfg.get("language") or ["en", "pt"]
    if isinstance(langs, str):
        langs = [langs]
    questions, commands = [], []
    for lang in langs:
        questions += QUESTION_MARKERS.get(str(lang).lower(), [])
        commands += COMMAND_MARKERS.get(str(lang).lower(), [])
    questions += [str(x).lower() for x in (cfg.get("extra_question_markers") or [])]
    commands += [str(x).lower() for x in (cfg.get("extra_command_markers") or [])]
    return questions, commands


def reflection_openers():
    cfg = gl.gate_config(GATE)
    langs = cfg.get("language") or ["en", "pt"]
    if isinstance(langs, str):
        langs = [langs]
    out = []
    for lang in langs:
        out += REFLECTION_OPENERS.get(str(lang).lower(), [])
    out += [str(x).lower() for x in (cfg.get("extra_reflection_openers") or [])]
    return out


# A determiner in front turns a verb into a noun: "the update failed" is a report,
# "update the config" is an instruction. Without this, a single-word imperative
# matches inside ordinary descriptions of what happened, and the gate stops
# protecting the message it exists for.
DETERMINERS = ("the", "a", "an", "this", "that", "these", "those", "my", "our",
               "its", "his", "her", "their", "your", "one", "each", "every",
               "o", "os", "as", "um", "uma", "esse", "essa", "este", "esta",
               "aquele", "aquela", "meu", "minha", "nosso", "nossa", "seu", "sua")


def _contains(text, marker):
    """True when `marker` appears as WHOLE WORDS, not as a substring.

    Substring matching gets this exactly backwards and silently. Measured while
    building this gate: "será que vale a pena FAZER isso" — a reflection — was
    classified as a command, because the command marker "faz" appears inside
    "fazer". The gate then stayed quiet on precisely the message it exists to
    catch.

    It is the same defect as an ignore list matching "scratch" inside
    "scratchpad", which had already been fixed once in this repository. A class
    of bug does not stop at the file where you first met it.

    Single-word markers additionally require that no determiner precedes them,
    so "the update failed last night" stays a report rather than becoming an
    instruction to update something.
    """
    pattern = r"(?<!\w)" + re.escape(marker) + r"(?!\w)"
    if " " in marker:
        return re.search(pattern, text) is not None
    for match in re.finditer(pattern, text):
        before = text[:match.start()].rstrip()
        last_word = re.split(r"\W+", before)[-1] if before else ""
        if last_word not in DETERMINERS:
            return True
    return False


def classify(message):
    """'command', 'question', or 'neutral'.

    An explicit instruction wins over everything: a message can end in a question
    mark and still be an order ("can you fix this?"). Reading the instruction
    first is what keeps this gate out of the way of ordinary work — and a gate
    that gets in the way of ordinary work is uninstalled within a week.
    """
    if not message:
        return "neutral"
    text = message.strip().lower()
    questions, commands = config()

    # Checked BEFORE the command markers: a reflection opener frames the whole
    # sentence, so an action verb appearing later belongs to the thing being
    # questioned, not to an instruction.
    if any(opener in text for opener in reflection_openers()):
        return "question"
    if any(_contains(text, marker) for marker in commands):
        return "command"
    if text.endswith("?"):
        return "question"
    if any(_contains(text, marker) for marker in questions):
        return "question"
    if re.search(r"\?\s", text) and len(text) < 400:
        return "question"
    return "neutral"


def handle(event):
    if gl.tool_name(event) not in ACTION_TOOLS:
        return                       # reading and searching are never blocked
    if classify(event.get("prompt") or "") != "question":
        return
    # One interruption per turn, not per action.
    if gl.already_flagged(GATE, event.get("session_id"), "turn"):
        return

    target = gl.target_path(event) or gl.bash_command(event)[:60]
    gl.deny(GATE, [
        "STOP — that message reads as a question, and this is an action.",
        "",
        "  about to: %s" % (target or gl.tool_name(event)),
        "",
        "A question is how someone thinks out loud. Executing it means the "
        "thinking had consequences nobody agreed to — and the real cost is not "
        "the wasted work, it is that people stop thinking out loud around you.",
        "",
        "Answer first: say what you understood, what you would do, and what it "
        "would change. Then they either confirm, or they tell you the thing you "
        "were about to get wrong.",
        "",
        "If it WAS an instruction, say so in one line and repeat — the rest of "
        "this turn runs normally. And an explicit instruction (\"do it\", \"go "
        "ahead\", \"fix it\") switches this gate off entirely.",
    ], target)


if __name__ == "__main__":
    gl.run(GATE, handle)
