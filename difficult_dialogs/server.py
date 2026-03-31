"""FastAPI REST server for difficult-dialogs.

Exposes structured debate sessions over HTTP so any frontend or service can
drive conversations without embedding Python.

Install extras::

    pip install difficult-dialogs[server]

Run::

    uvicorn difficult_dialogs.server:app --reload
    # or
    dd serve --host 0.0.0.0 --port 8080 --args-dir examples/sample_arguments

Endpoints
---------
POST /sessions
    Start a new session for a given argument path or pre-loaded name.
    Returns session_id + intro text.

POST /sessions/{session_id}/chat
    Send a user message; receive bot response.

GET  /sessions/{session_id}
    Retrieve full session state (transcript, finished flag, current premise).

DELETE /sessions/{session_id}
    Discard a session.

GET  /arguments
    List all available arguments in the configured arguments directory.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "FastAPI and Pydantic are required for the REST server. "
        "Install with: pip install difficult-dialogs[server]"
    ) from exc

from difficult_dialogs.arguments import Argument
from difficult_dialogs.policy import (
    BasePolicy,
    KnowItAllPolicy,
    POLICY_REGISTRY,
)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class StartRequest(BaseModel):
    """Request body for POST /sessions."""
    argument_path: str
    policy: str = "knowitall"


class ChatRequest(BaseModel):
    """Request body for POST /sessions/{session_id}/chat."""
    message: str


class TranscriptEntryModel(BaseModel):
    """A single conversation turn."""
    role: str
    text: str


class SessionResponse(BaseModel):
    """Full session state returned by GET /sessions/{session_id}."""
    session_id: str
    argument: str
    policy: str
    finished: bool
    current_premise: str | None
    transcript: list[TranscriptEntryModel]


class StartResponse(BaseModel):
    """Response to POST /sessions."""
    session_id: str
    intro: str


class ChatResponse(BaseModel):
    """Response to POST /sessions/{session_id}/chat."""
    response: str | None
    finished: bool


# ---------------------------------------------------------------------------
# In-process session store
# ---------------------------------------------------------------------------

class _Session:
    """Holds one active policy instance."""

    def __init__(self, policy: BasePolicy, policy_name: str) -> None:
        self.policy = policy
        self.policy_name = policy_name
        self.started = False


_sessions: dict[str, _Session] = {}


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Difficult Dialogs API",
    description="Structured debate sessions over HTTP.",
    version="0.5.0",
)


@app.post("/sessions", response_model=StartResponse, status_code=201)
def create_session(req: StartRequest) -> Any:
    """Start a new debate session.

    Args:
        req.argument_path: Filesystem path to the argument directory.
        req.policy: Policy name (default ``knowitall``).

    Returns:
        ``session_id`` and the argument's ``intro`` text.
    """
    path = Path(req.argument_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Argument path not found: {path}")

    try:
        arg = Argument.from_directory(path)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    policy_name = req.policy.lower().strip()
    if policy_name not in POLICY_REGISTRY:
        available = ", ".join(POLICY_REGISTRY)
        raise HTTPException(
            status_code=422,
            detail=f"Unknown policy {policy_name!r}. Available: {available}",
        )

    policy_cls = POLICY_REGISTRY[policy_name]
    policy = policy_cls(arg)
    intro = policy.start()

    session_id = str(uuid.uuid4())
    _sessions[session_id] = _Session(policy=policy, policy_name=policy_name)
    _sessions[session_id].started = True

    return StartResponse(session_id=session_id, intro=intro)


@app.post("/sessions/{session_id}/chat", response_model=ChatResponse)
def chat(session_id: str, req: ChatRequest) -> Any:
    """Send a user message and receive the bot's response.

    Args:
        session_id: ID returned by POST /sessions.
        req.message: User's text input.

    Returns:
        ``response`` text (may be ``None`` if policy needs more input) and
        ``finished`` flag.
    """
    session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    response = session.policy.respond(req.message)
    return ChatResponse(
        response=response,
        finished=session.policy.state.finished,
    )


@app.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str) -> Any:
    """Retrieve full session state including transcript.

    Args:
        session_id: ID returned by POST /sessions.
    """
    session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    state = session.policy.state
    return SessionResponse(
        session_id=session_id,
        argument=session.policy.argument.name,
        policy=session.policy_name,
        finished=state.finished,
        current_premise=state.current_premise,
        transcript=[
            TranscriptEntryModel(role=e.role, text=e.text)
            for e in state.transcript
        ],
    )


@app.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: str) -> None:
    """Discard a session and free its memory.

    Args:
        session_id: ID returned by POST /sessions.
    """
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    del _sessions[session_id]


@app.get("/arguments")
def list_arguments(args_dir: str = "examples/sample_arguments") -> Any:
    """List argument directories available under *args_dir*.

    Args:
        args_dir: Root directory to scan (query parameter, default
                  ``examples/sample_arguments``).

    Returns:
        Mapping of ``{category: [argument_name, …], …}``.
    """
    root = Path(args_dir)
    if not root.exists():
        raise HTTPException(status_code=404, detail=f"Directory not found: {root}")

    result: dict[str, list[str]] = {}
    for category_dir in sorted(root.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith("."):
            continue
        names = [
            d.name
            for d in sorted(category_dir.iterdir())
            if d.is_dir() and (d / "intro.dialog").exists()
        ]
        if names:
            result[category_dir.name] = names

    return result
