"""Web server: connects the chat frontend to the orchestrator.

Run it with:
    uvicorn backend.app:app --reload
Then open http://localhost:8000
"""
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend import llm
from backend import orchestrator as orch
from backend.content import GREETING, NO_LLM_MESSAGE

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s: %(message)s")
logging.getLogger("orchestrator").info("LLM: %s", llm.describe())

app = FastAPI(title="Pre-consultation Chatbot")
# session_id -> {"state": conversation state, "history": turns sent to the LLM}
SESSIONS: dict[str, dict] = {}


class ChatIn(BaseModel):
    session_id: str
    message: str


class ResetIn(BaseModel):
    session_id: str


def new_session():
    return {"state": orch.new_state(), "history": []}


@app.post("/api/reset")
def reset(body: ResetIn):
    SESSIONS[body.session_id] = new_session()
    greeting = GREETING if llm.enabled() else NO_LLM_MESSAGE
    return {"reply": greeting, "state": SESSIONS[body.session_id]["state"],
            "action": None, "decided_by": None, "llm": llm.describe()}


@app.post("/api/chat")
def chat(body: ChatIn):
    session = SESSIONS.setdefault(body.session_id, new_session())
    state = session["state"]
    try:
        reply = orch.handle(body.message, state, session["history"])
        action = state.get("last_action") or "not_routed"
    except Exception as e:  # show errors in the chat instead of crashing
        logging.exception("Orchestrator error")
        reply, action = f"[Error in orchestrator: {type(e).__name__}: {e}]", "error"
    decided_by = "llm" if action not in ("no_llm", "unavailable", "error", "not_routed") else None
    return {"reply": reply, "state": state, "action": action, "decided_by": decided_by}


# Serve the frontend (must come after the API routes)
FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
