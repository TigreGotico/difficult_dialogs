"""Unit tests for difficult_dialogs.statements.Statement."""
import pytest
from difficult_dialogs.statements import Statement


def test_default_true() -> None:
    s = Statement("hello world")
    assert s.text == "hello world"
    assert s.is_true is True
    assert bool(s) is True


def test_str() -> None:
    s = Statement("test text")
    assert str(s) == "test text"


def test_disagree_sets_false() -> None:
    s = Statement("claim")
    s.disagree()
    assert s.is_true is False
    assert bool(s) is False


def test_agree_restores_true() -> None:
    s = Statement("claim")
    s.disagree()
    s.agree()
    assert s.is_true is True


def test_initial_false() -> None:
    s = Statement("claim", is_true=False)
    assert bool(s) is False


def test_from_json_updates_fields() -> None:
    s = Statement("old")
    s.from_json({"text": "new text", "is_true": False})
    assert s.text == "new text"
    assert s.is_true is False


def test_from_json_defaults() -> None:
    s = Statement("old")
    s.from_json({})
    assert s.text == ""
    assert s.is_true is True


def test_as_json_roundtrip() -> None:
    s = Statement("roundtrip", is_true=False)
    data = s.as_json
    assert data == {"text": "roundtrip", "is_true": False}
    s2 = Statement("x")
    s2.from_json(data)
    assert s2.text == "roundtrip"
    assert s2.is_true is False
