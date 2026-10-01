# National University of Singapore  · CS3249 · Conversational User Interface · Tutorial 4: Conversation Orchestration

## Exercise Intro: Pre-consultation Chatbot

In this exercise you turn a chatbot that only talks into one that remembers and decides.

The initial chatbot already works. An LLM, guided by a system prompt, chats with a student before their first counselling session. But the program around it does nothing yet:

it keeps no state, so the conversation state panel is empty and nothing is recorded for the counsellor
it does no routing: whatever the LLM decides is ignored, and its reply is sent as it is

Your job is to add the conversation state (Activity 1) and the routing (Activity 2) in backend/orchestrator.py.. Together, they are the orchestration layer from the lecture: the LLM proposes, your code decides.


---
### What you will need 
1. Python 3.10 or newer. Check with python3 --version (macOS/Linux) or python --version (Windows).
2. LLM API Key 
   - You can apply through : SoCLaaS is SoC’s locally hosted, OpenAI-compatible LLM API service. It provides SoC students with free-of-charge access to open-weight LLM models for learning, coursework, experimentation, prototypes, and development project

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate    # Windows: python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Add your API key at the top of `backend/llm.py`:

```python
LLM_PROVIDER = "anthropic"
ANTHROPIC_API_KEY = "sk-ant-..."
```

Run the server and open **http://localhost:8000**. Stop it with **Ctrl + C**.

```bash
python -m uvicorn backend.app:app --reload
```

Try the **Test script** buttons. The bot replies, but the state panel is empty and the decision shows `not_routed`.

## Activity 1: State 

1. **`new_state()`:** return a dict with these fields:
   - the four slots in `STEPS`, each `None`
   - `current_step`, starting at `"reason_for_visit"`
   - `risk_flag` (`False`), `skipped` (`[]`) and `last_action` (`None`)
2. **`next_step(state)`:** return the first slot that is still `None`, or `"done"`.
3. **`turn_message()`:** fill in `TURN_TEMPLATE` with the items collected, the items missing, the skipped items and the message.

## Activity 2: Routing 

In `handle()`, replace the TODO with these steps, in this order:

1. **`escalate`:** set `risk_flag` and return `CRISIS_MESSAGE`. Change nothing else.
2. Save `d["updates"]` into the state.
3. Set each item in `d["skipped"]` to `DECLINED` and add it to `skipped`.
4. `current_step = next_step(state)`
5. `last_action = d["action"]`
6. Reply with `d["reply"]`. If it's empty, use `QUESTIONS[current_step]`, or `DONE_MESSAGE` once the intake is done.

**Done when** the test script ends with:
- all four slots filled
- `duration` showing the corrected value, 2 months
- `current_step` at `done`

## Check

```bash
pytest
```

You start at 8 passing. After Activity 1, 11 pass. When both activities are done, all 22 pass.

#### Check starter file 
```bash
python -m pytest tests/test_starter.py -v
```
#### Run one test only 
```bash
python -m pytest -v -k test_starter_failures_are_handled
```

## If something breaks

- **No key, or a connection error:** check `llm.py`, then restart the server.
- **`bad interpreter`:** delete `.venv` and redo the setup.
- **`No module named …`:** activate `.venv`, then run `pip install -r requirements.txt`.

> This is a teaching prototype. Use only made-up messages, never real personal information.