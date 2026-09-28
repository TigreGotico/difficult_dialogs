"""Tests for the example FastAPI REST server (examples/server.py)."""
import sys
import pytest
from pathlib import Path

pytest.importorskip("fastapi", reason="fastapi not installed — skipping server tests")
pytest.importorskip("httpx", reason="httpx not installed — skipping server tests")

import importlib.util  # noqa: E402

_server_path = Path(__file__).parent.parent / "examples" / "server.py"
_spec = importlib.util.spec_from_file_location("_dd_server_test", _server_path)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

from fastapi.testclient import TestClient  # noqa: E402

app = _mod.app
_sessions = _mod._sessions

COGITO_DIR = str(Path(__file__).parent.parent / "examples" / "i_think_therefore_i_am")

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_sessions():
    """Reset the in-process session store before each test."""
    _sessions.clear()
    yield
    _sessions.clear()


# ---------------------------------------------------------------------------
# POST /sessions
# ---------------------------------------------------------------------------

def test_create_session_returns_session_id_and_intro() -> None:
    resp = client.post("/sessions", json={"argument_path": COGITO_DIR})
    assert resp.status_code == 201
    data = resp.json()
    assert "session_id" in data
    assert "intro" in data
    assert data["intro"]


def test_create_session_bad_path() -> None:
    resp = client.post("/sessions", json={"argument_path": "/does/not/exist"})
    assert resp.status_code == 404


def test_create_session_bad_policy() -> None:
    resp = client.post("/sessions", json={
        "argument_path": COGITO_DIR,
        "policy": "nonexistent_policy",
    })
    assert resp.status_code == 422


def test_create_session_default_policy_is_knowitall() -> None:
    resp = client.post("/sessions", json={"argument_path": COGITO_DIR})
    assert resp.status_code == 201
    session_id = resp.json()["session_id"]
    session_resp = client.get(f"/sessions/{session_id}")
    assert session_resp.json()["policy"] == "knowitall"


def test_create_session_custom_policy() -> None:
    resp = client.post("/sessions", json={
        "argument_path": COGITO_DIR,
        "policy": "silent",
    })
    assert resp.status_code == 201
    session_id = resp.json()["session_id"]
    session_resp = client.get(f"/sessions/{session_id}")
    assert session_resp.json()["policy"] == "silent"


# ---------------------------------------------------------------------------
# POST /sessions/{session_id}/chat
# ---------------------------------------------------------------------------

def test_chat_returns_response() -> None:
    session_id = client.post("/sessions", json={"argument_path": COGITO_DIR}).json()["session_id"]
    resp = client.post(f"/sessions/{session_id}/chat", json={"message": "yes"})
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    assert "finished" in data


def test_chat_unknown_session() -> None:
    resp = client.post("/sessions/nonexistent/chat", json={"message": "hi"})
    assert resp.status_code == 404


def test_chat_transcript_grows() -> None:
    session_id = client.post("/sessions", json={"argument_path": COGITO_DIR}).json()["session_id"]
    client.post(f"/sessions/{session_id}/chat", json={"message": "yes"})
    client.post(f"/sessions/{session_id}/chat", json={"message": "yes"})
    state = client.get(f"/sessions/{session_id}").json()
    assert len(state["transcript"]) >= 3  # intro + 2 user turns (at minimum)


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}
# ---------------------------------------------------------------------------

def test_get_session_returns_state() -> None:
    session_id = client.post("/sessions", json={"argument_path": COGITO_DIR}).json()["session_id"]
    resp = client.get(f"/sessions/{session_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == session_id
    assert data["argument"]
    assert isinstance(data["transcript"], list)
    assert isinstance(data["finished"], bool)


def test_get_session_includes_progress() -> None:
    """GET /sessions/{id} returns progress_covered and progress_total."""
    session_id = client.post("/sessions", json={"argument_path": COGITO_DIR}).json()["session_id"]
    data = client.get(f"/sessions/{session_id}").json()
    assert "progress_covered" in data
    assert "progress_total" in data
    assert isinstance(data["progress_covered"], int)
    assert isinstance(data["progress_total"], int)
    assert data["progress_total"] > 0


def test_get_session_unknown() -> None:
    resp = client.get("/sessions/doesnotexist")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /sessions/{session_id}
# ---------------------------------------------------------------------------

def test_delete_session() -> None:
    session_id = client.post("/sessions", json={"argument_path": COGITO_DIR}).json()["session_id"]
    resp = client.delete(f"/sessions/{session_id}")
    assert resp.status_code == 204
    assert client.get(f"/sessions/{session_id}").status_code == 404


def test_delete_unknown_session() -> None:
    resp = client.delete("/sessions/ghost")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /arguments
# ---------------------------------------------------------------------------

def test_list_arguments() -> None:
    sample_dir = str(Path(__file__).parent.parent / "examples" / "sample_arguments")
    resp = client.get(f"/arguments?args_dir={sample_dir}")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert len(data) > 0
    # At least one category has arguments
    assert any(len(v) > 0 for v in data.values())


def test_list_arguments_bad_dir() -> None:
    resp = client.get("/arguments?args_dir=/no/such/path")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /sessions/{id}/state  &  PUT /sessions/{id}/state
# ---------------------------------------------------------------------------

def test_get_state_returns_serialised_state() -> None:
    session_id = client.post("/sessions", json={"argument_path": COGITO_DIR}).json()["session_id"]
    client.post(f"/sessions/{session_id}/chat", json={"message": "yes"})
    resp = client.get(f"/sessions/{session_id}/state")
    assert resp.status_code == 200
    data = resp.json()
    assert "spoken_premises" in data
    assert "transcript" in data
    assert isinstance(data["transcript"], list)


def test_restore_state_resumes_session() -> None:
    """Export state from one session, restore into another, continue chatting."""
    sid1 = client.post("/sessions", json={"argument_path": COGITO_DIR}).json()["session_id"]
    client.post(f"/sessions/{sid1}/chat", json={"message": "yes"})
    state = client.get(f"/sessions/{sid1}/state").json()

    # New session for the same argument — restore snapshot
    sid2 = client.post("/sessions", json={"argument_path": COGITO_DIR}).json()["session_id"]
    resp = client.put(f"/sessions/{sid2}/state", json=state)
    assert resp.status_code == 204

    # The restored session should have the same spoken premises
    restored = client.get(f"/sessions/{sid2}/state").json()
    assert set(restored["spoken_premises"]) == set(state["spoken_premises"])


def test_get_state_unknown_session() -> None:
    resp = client.get("/sessions/ghost/state")
    assert resp.status_code == 404


def test_put_state_unknown_session() -> None:
    resp = client.put("/sessions/ghost/state", json={})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# WebSocket /sessions/{id}/ws
# ---------------------------------------------------------------------------

def test_ws_unknown_session_closes() -> None:
    """WebSocket to unknown session is rejected with a close code."""
    from starlette.websockets import WebSocketDisconnect
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/sessions/ghost/ws") as ws:
            pass


def test_ws_sends_intro_on_connect() -> None:
    """WebSocket sends intro JSON immediately after connect."""
    import json
    session_id = client.post("/sessions", json={"argument_path": COGITO_DIR}).json()["session_id"]
    with client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        msg = json.loads(ws.receive_text())
        assert "response" in msg
        assert "finished" in msg
        assert "progress_covered" in msg
        assert "progress_total" in msg
        assert msg["progress_total"] > 0


def test_ws_full_turn() -> None:
    """WebSocket round-trip: send a turn, receive a response."""
    import json
    session_id = client.post("/sessions", json={"argument_path": COGITO_DIR}).json()["session_id"]
    with client.websocket_connect(f"/sessions/{session_id}/ws") as ws:
        ws.receive_text()  # consume intro
        ws.send_text("yes")
        reply = json.loads(ws.receive_text())
        assert "response" in reply
        assert isinstance(reply["finished"], bool)
