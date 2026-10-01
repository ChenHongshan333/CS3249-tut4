"""[starter] checks: these pass BEFORE you change anything."""
import json

import pytest

from backend import llm
from backend import orchestrator as orch
from backend.content import NO_LLM_MESSAGE, UNAVAILABLE_MESSAGE
from backend.prompts import SYSTEM_PROMPT


@pytest.fixture
def fake(monkeypatch):
    def install(*responses):
        calls = []

        def chat_json(system, messages, max_tokens=500):
            calls.append({"system": system, "messages": [dict(m) for m in messages]})
            r = responses[len(calls) - 1]
            if isinstance(r, Exception):
                raise r
            return r

        monkeypatch.setenv("LLM_PROVIDER", "anthropic")
        monkeypatch.setattr(llm, "chat_json", chat_json)
        return calls
    return install


def say(reply, action="fill_slot", updates=None):
    return {"action": action, "updates": updates or {}, "skipped": [], "reply": reply}


def test_starter_llm_reply_reaches_the_student(fake):
    fake(say("Thanks for sharing. How long have you felt this way?"))
    assert orch.handle("Stressed about exams", orch.new_state()) == \
        "Thanks for sharing. How long have you felt this way?"


def test_starter_llm_gets_system_prompt_and_history(fake):
    calls = fake(say("How long?"), say("And from 1 to 10?"))
    state, history = orch.new_state(), []
    orch.handle("Stressed about exams", state, history)
    orch.handle("About 3 weeks", state, history)
    assert calls[1]["system"] == SYSTEM_PROMPT
    assert [m["role"] for m in calls[1]["messages"]] == ["user", "assistant", "user"]


def test_starter_state_is_json(fake):
    fake(say("How long?", updates={"reason_for_visit": "exams"}))
    state = orch.new_state()
    orch.handle("exams", state)
    json.dumps(state)


def test_starter_failures_are_handled(fake):
    fake(llm.LLMError("timeout"))
    assert orch.handle("hi", orch.new_state()) == UNAVAILABLE_MESSAGE


def test_starter_no_llm_configured():
    assert orch.handle("hi", orch.new_state()) == NO_LLM_MESSAGE