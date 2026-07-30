"""Tests for difficult_dialogs.yesno fuzzy yes/no detection."""
import pytest
from unittest.mock import MagicMock
import difficult_dialogs.yesno as yesno_module
from difficult_dialogs.yesno import (
    parse_yes_no,
    is_agreement,
    is_disagreement,
    set_solver,
    _load_solver,
)


@pytest.fixture(autouse=True)
def reset_solver():
    """Reset the module-level solver singleton after each test."""
    original = yesno_module._solver
    yield
    yesno_module._solver = original


def _make_solver(result: bool | None) -> MagicMock:
    m = MagicMock()
    m.match_yes_or_no.return_value = result
    return m


# ---------------------------------------------------------------------------
# set_solver — delegates to custom solver
# ---------------------------------------------------------------------------

def test_set_solver_true() -> None:
    set_solver(_make_solver(True))
    assert parse_yes_no("whatever") is True


def test_set_solver_false() -> None:
    set_solver(_make_solver(False))
    assert parse_yes_no("whatever") is False


def test_set_solver_none() -> None:
    set_solver(_make_solver(None))
    assert parse_yes_no("whatever") is None


def test_set_solver_receives_text_and_lang() -> None:
    mock = _make_solver(True)
    set_solver(mock)
    parse_yes_no("oui", lang="fr-FR")
    mock.match_yes_or_no.assert_called_once_with("oui", "fr-FR")


# ---------------------------------------------------------------------------
# _load_solver — entry-point discovery
# ---------------------------------------------------------------------------

def _make_ep(name: str, instance: object) -> MagicMock:
    ep = MagicMock()
    ep.name = name
    ep.load.return_value = lambda: instance
    return ep


def test_load_solver_prefers_named_plugin(monkeypatch) -> None:
    preferred = _make_solver(True)
    other = _make_solver(False)
    ep_preferred = _make_ep("ovos-solver-yes-no-plugin", preferred)
    ep_other = _make_ep("some-other-plugin", other)
    monkeypatch.setattr(
        "importlib.metadata.entry_points",
        lambda group: [ep_other, ep_preferred],
    )
    solver = _load_solver("ovos-solver-yes-no-plugin")
    assert solver is preferred


def test_load_solver_falls_back_to_any_plugin(monkeypatch) -> None:
    fallback = _make_solver(None)
    ep = _make_ep("other-plugin", fallback)
    monkeypatch.setattr(
        "importlib.metadata.entry_points",
        lambda group: [ep],
    )
    solver = _load_solver("missing-plugin")
    assert solver is fallback


def test_load_solver_raises_when_no_plugins(monkeypatch) -> None:
    monkeypatch.setattr(
        "importlib.metadata.entry_points",
        lambda group: [],
    )
    with pytest.raises(RuntimeError, match="opm.agents.yesno"):
        _load_solver()


def test_load_solver_skips_broken_plugin(monkeypatch) -> None:
    good = _make_solver(True)
    bad_ep = MagicMock()
    bad_ep.name = "ovos-solver-yes-no-plugin"
    bad_ep.load.side_effect = ImportError("missing dep")
    good_ep = _make_ep("good-plugin", good)
    monkeypatch.setattr(
        "importlib.metadata.entry_points",
        lambda group: [bad_ep, good_ep],
    )
    solver = _load_solver("ovos-solver-yes-no-plugin")
    assert solver is good


# ---------------------------------------------------------------------------
# _load_solver — yes_or_no (YesNoEngine) API adapter
# ---------------------------------------------------------------------------

class _FakeYesNoEngine:
    """Engine exposing only the ``yes_or_no(question, response, lang)`` API."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def yes_or_no(self, question: str, response: str, lang: str = "en-US") -> bool | None:
        self.calls.append((question, response, lang))
        return "yes" in response


def test_load_solver_adapts_yes_or_no_engine(monkeypatch) -> None:
    engine = _FakeYesNoEngine()
    ep = _make_ep("ovos-yes-no-plugin", engine)
    monkeypatch.setattr(
        "importlib.metadata.entry_points",
        lambda group: [ep],
    )
    solver = _load_solver()
    assert solver.match_yes_or_no("yes please", "en-US") is True
    assert solver.match_yes_or_no("nah", "en-US") is False
    # the adapter passes the text as the response with an empty question
    assert engine.calls[0] == ("", "yes please", "en-US")


def test_load_solver_prefers_match_yes_or_no_over_adapter(monkeypatch) -> None:
    native = _make_solver(True)
    engine = _FakeYesNoEngine()
    ep_native = _make_ep("ovos-yes-no-plugin", native)
    ep_engine = _make_ep("some-engine-plugin", engine)
    monkeypatch.setattr(
        "importlib.metadata.entry_points",
        lambda group: [ep_engine, ep_native],
    )
    solver = _load_solver()
    assert solver is native


def test_load_solver_skips_object_without_either_api(monkeypatch) -> None:
    class _Useless:
        pass

    engine = _FakeYesNoEngine()
    ep_useless = _make_ep("ovos-yes-no-plugin", _Useless())
    ep_engine = _make_ep("zz-engine-plugin", engine)
    monkeypatch.setattr(
        "importlib.metadata.entry_points",
        lambda group: [ep_useless, ep_engine],
    )
    solver = _load_solver()
    assert solver.match_yes_or_no("yes", "en-US") is True


# ---------------------------------------------------------------------------
# is_agreement / is_disagreement helpers
# ---------------------------------------------------------------------------

def test_is_agreement_true() -> None:
    set_solver(_make_solver(True))
    assert is_agreement("yes") is True


def test_is_agreement_false_on_no() -> None:
    set_solver(_make_solver(False))
    assert is_agreement("no") is False


def test_is_agreement_default_true_on_ambiguous() -> None:
    set_solver(_make_solver(None))
    assert is_agreement("hmm", default=True) is True


def test_is_agreement_default_false_on_ambiguous() -> None:
    set_solver(_make_solver(None))
    assert is_agreement("hmm", default=False) is False


def test_is_disagreement_true_on_no() -> None:
    set_solver(_make_solver(False))
    assert is_disagreement("nope") is True


def test_is_disagreement_false_on_yes() -> None:
    set_solver(_make_solver(True))
    assert is_disagreement("yeah") is False


def test_is_disagreement_default_false_on_ambiguous() -> None:
    set_solver(_make_solver(None))
    assert is_disagreement("whatever", default=False) is False


def test_is_disagreement_default_true_on_ambiguous() -> None:
    set_solver(_make_solver(None))
    assert is_disagreement("whatever", default=True) is True


# ---------------------------------------------------------------------------
# Integration — actual ovos-solver-yes-no-plugin (skipped if not loadable)
# ---------------------------------------------------------------------------

def _real_solver_available() -> bool:
    try:
        from difficult_dialogs.yesno import _load_solver
        _load_solver()
        return True
    except RuntimeError:
        return False


_skip_integration = pytest.mark.skipif(
    not _real_solver_available(),
    reason="ovos-solver-yes-no-plugin opm.agents.yesno entry-point not available",
)


@_skip_integration
def test_integration_yes() -> None:
    yesno_module._solver = None
    assert parse_yes_no("yes") is True


@_skip_integration
def test_integration_no() -> None:
    yesno_module._solver = None
    assert parse_yes_no("nope") is False


@_skip_integration
def test_integration_ambiguous() -> None:
    yesno_module._solver = None
    assert parse_yes_no("hmm") is None


@_skip_integration
def test_integration_agree_phrase() -> None:
    yesno_module._solver = None
    assert parse_yes_no("I agree") is True


@_skip_integration
def test_integration_disagree_phrase() -> None:
    yesno_module._solver = None
    assert parse_yes_no("I disagree") is False
