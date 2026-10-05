"""Tutorial 2: Conversation Orchestration  —  Student VERSION

The LLM handles the conversation content, guided by the system prompt in
backend/prompts.py: it understands each message, picks an action and writes
the reply. There is no rule-based router.

This file keeps what the LLM should NOT own:
  - the conversation STATE (Activity 1), shown live in the browser
  - VALIDATION of every LLM decision before it touches the state
  - the fixed crisis message when the LLM escalates

The LLM proposes. This code decides what is allowed and what is remembered.
"""
import json
import logging

from backend import llm
from backend.content import (
    CRISIS_MESSAGE, DONE_MESSAGE, NO_LLM_MESSAGE, QUESTIONS, STEPS,
    UNAVAILABLE_MESSAGE,
)
from backend.prompts import SYSTEM_PROMPT, TURN_TEMPLATE

log = logging.getLogger("orchestrator")

ACTIONS = {"fill_slot", "answer_faq", "update_info", "skip", "escalate", "other"}
DECLINED = "(prefers not to say)"
MAX_VALUE_CHARS = 200
MAX_REPLY_CHARS = 800
HISTORY_TURNS = 12          # messages of history sent to the LLM (6 exchanges)


# ==========================================================================
# Activity 1: conversation state
# ==========================================================================
def new_state():
    """Create JSON-serializable memory for a new conversation."""
    return {
        **{step: None for step in STEPS},
        "current_step": STEPS[0],
        "risk_flag": False,
        "skipped": [],
        "last_action": None,
    }


def next_step(state):
    """Return the first unanswered slot in order, or "done"."""
    for step in STEPS:
        if state[step] is None:
            return step
    return "done"

def turn_message(message, state):
    """Send the recorded state and latest student message to the LLM."""
    skipped = [step for step in STEPS if step in state["skipped"]]
    collected = {
        step: state[step] for step in STEPS
        if state[step] is not None and step not in skipped
    }
    missing = [
        step for step in STEPS
        if state[step] is None and step not in skipped
    ]
    return TURN_TEMPLATE.format(
        collected=json.dumps(collected, ensure_ascii=False),
        missing=json.dumps(missing, ensure_ascii=False),
        skipped=json.dumps(skipped, ensure_ascii=False),
        message=message,
    )


# ==========================================================================
# Activity 2: the LLM decides the action; the code validates and applies it
# ==========================================================================
def validate(raw):
    """Never trust the LLM blindly: keep only known actions, item names and sizes."""
    action = raw.get("action") if raw.get("action") in ACTIONS else "other"
    updates = raw.get("updates") if isinstance(raw.get("updates"), dict) else {}
    skipped = raw.get("skipped") if isinstance(raw.get("skipped"), list) else []
    reply = raw.get("reply") if isinstance(raw.get("reply"), str) else ""
    return {
        "action": action,
        "updates": {
            k: str(v).strip()[:MAX_VALUE_CHARS]
            for k, v in updates.items()
            if k in STEPS and v is not None and str(v).strip()
        },
        "skipped": [s for s in skipped if s in STEPS],
        "reply": reply.strip()[:MAX_REPLY_CHARS],
    }


def handle(message, state, history=None):
    """Run one turn and return the bot's reply.

    state   : the conversation state (YOUR job to update, Activity 2)
    history : list of earlier {"role", "content"} turns (kept by the server)
    """
    history = history if history is not None else []

    if not llm.enabled():
        return NO_LLM_MESSAGE

    messages = history[-HISTORY_TURNS:] + [{"role": "user", "content": turn_message(message, state)}]
    try:
        d = validate(llm.chat_json(SYSTEM_PROMPT, messages))
    except llm.LLMError as e:
        log.warning("LLM call failed: %s", e)
        return UNAVAILABLE_MESSAGE

    if d["action"] == "escalate":
        state["risk_flag"] = True
        return CRISIS_MESSAGE

    state.update(d["updates"])
    for step in d["skipped"]:
        state[step] = DECLINED
        if step not in state["skipped"]:
            state["skipped"].append(step)

    state["current_step"] = next_step(state)
    state["last_action"] = d["action"]
    reply = d["reply"] or (
        DONE_MESSAGE if state["current_step"] == "done"
        else QUESTIONS[state["current_step"]]
    )

    # Remember the turn so the LLM sees the conversation so far.
    history.append({"role": "user", "content": messages[-1]["content"]})
    history.append({"role": "assistant", "content": json.dumps({**d, "reply": reply})})
    return reply
