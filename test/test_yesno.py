"""Tests for difficult_dialogs.yesno fuzzy yes/no detection."""
import pytest
from unittest.mock import MagicMock
import difficult_dialogs.yesno as yesno_module
from difficult_dialogs.yesno import (
    parse_yes_no,
    is_agreement,
    is_disagreement,
    set_solver,
    _BuiltinYesNoSolver,
    _load_solver,
)


@pytest.fixture(autouse=True)
def reset_solver():
    """Reset the module-level solver singleton after each test."""
    original = yesno_module._solver
    yield
    yesno_module._solver = original


# ---------------------------------------------------------------------------
# _BuiltinYesNoSolver — strong yes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "yes", "Yes", "YES",
    "yeah", "yep", "yup",
    "correct", "confirmed", "agree", "agreed",
    "absolutely", "indeed", "affirmative",
    "I agree with that",
    "that's correct",
    "yes I think so",
    "yep that sounds right",
])
def test_builtin_strong_yes(text: str) -> None:
    s = _BuiltinYesNoSolver()
    assert s.match_yes_or_no(text, "en-US") is True


# ---------------------------------------------------------------------------
# _BuiltinYesNoSolver — strong no
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "no", "No", "NO",
    "nope", "nah",
    "negative",
    "disagree", "I disagree",
    "incorrect", "false",
    "I don't agree",
    "nope not at all",
])
def test_builtin_strong_no(text: str) -> None:
    s = _BuiltinYesNoSolver()
    assert s.match_yes_or_no(text, "en-US") is False


# ---------------------------------------------------------------------------
# _BuiltinYesNoSolver — neutral yes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "sure", "certainly", "definitely",
    "of course", "fine", "alright",
])
def test_builtin_neutral_yes(text: str) -> None:
    s = _BuiltinYesNoSolver()
    assert s.match_yes_or_no(text, "en-US") is True


# ---------------------------------------------------------------------------
# _BuiltinYesNoSolver — neutral no
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "that's wrong", "that seems mistaken",
    "that's a lie",
])
def test_builtin_neutral_no(text: str) -> None:
    s = _BuiltinYesNoSolver()
    assert s.match_yes_or_no(text, "en-US") is False


# ---------------------------------------------------------------------------
# _BuiltinYesNoSolver — ambiguous / neutral
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "I don't know",
    "maybe",
    "hmm",
    "",
    "what do you mean",
])
def test_builtin_ambiguous_returns_none(text: str) -> None:
    s = _BuiltinYesNoSolver()
    assert s.match_yes_or_no(text, "en-US") is None


# ---------------------------------------------------------------------------
# _BuiltinYesNoSolver — last word wins / double negatives
# ---------------------------------------------------------------------------

def test_builtin_yes_then_no_returns_no() -> None:
    s = _BuiltinYesNoSolver()
    assert s.match_yes_or_no("yes wait no", "en-US") is False


def test_builtin_no_then_yes_returns_yes() -> None:
    s = _BuiltinYesNoSolver()
    assert s.match_yes_or_no("no actually yes", "en-US") is True


def test_builtin_double_negative_not_wrong_is_yes() -> None:
    s = _BuiltinYesNoSolver()
    assert s.match_yes_or_no("that's not wrong", "en-US") is True


# ---------------------------------------------------------------------------
# set_solver — delegates to custom solver
# ---------------------------------------------------------------------------

def test_set_solver_used_for_parse() -> None:
    mock_solver = MagicMock()
    mock_solver.match_yes_or_no.return_value = True
    set_solver(mock_solver)
    result = parse_yes_no("whatever")
    mock_solver.match_yes_or_no.assert_called_once_with("whatever", "en-US")
    assert result is True


def test_set_solver_false() -> None:
    mock_solver = MagicMock()
    mock_solver.match_yes_or_no.return_value = False
    set_solver(mock_solver)
    assert parse_yes_no("whatever") is False


def test_set_solver_none_neutral() -> None:
    mock_solver = MagicMock()
    mock_solver.match_yes_or_no.return_value = None
    set_solver(mock_solver)
    assert parse_yes_no("whatever") is None


# ---------------------------------------------------------------------------
# _load_solver — fallback to builtin when no plugins available
# ---------------------------------------------------------------------------

def test_load_solver_falls_back_to_builtin(monkeypatch) -> None:
    monkeypatch.setattr(
        "importlib.metadata.entry_points",
        lambda group: [],
    )
    monkeypatch.setattr(yesno_module, "_import_default_solver", lambda: None)
    solver = _load_solver()
    assert isinstance(solver, _BuiltinYesNoSolver)


def test_load_solver_skips_broken_plugin(monkeypatch) -> None:
    broken_ep = MagicMock()
    broken_ep.name = "broken-plugin"
    broken_ep.load.side_effect = ImportError("missing dep")
    monkeypatch.setattr(
        "importlib.metadata.entry_points",
        lambda group: [broken_ep],
    )
    monkeypatch.setattr(yesno_module, "_import_default_solver", lambda: None)
    solver = _load_solver()
    assert isinstance(solver, _BuiltinYesNoSolver)


# ---------------------------------------------------------------------------
# is_agreement / is_disagreement helpers
# ---------------------------------------------------------------------------

def test_is_agreement_true_on_yes() -> None:
    set_solver(_BuiltinYesNoSolver())
    assert is_agreement("yes") is True


def test_is_agreement_false_on_no() -> None:
    set_solver(_BuiltinYesNoSolver())
    assert is_agreement("no") is False


def test_is_agreement_default_on_ambiguous() -> None:
    set_solver(_BuiltinYesNoSolver())
    assert is_agreement("hmm", default=True) is True
    assert is_agreement("hmm", default=False) is False


def test_is_disagreement_true_on_no() -> None:
    set_solver(_BuiltinYesNoSolver())
    assert is_disagreement("nope") is True


def test_is_disagreement_false_on_yes() -> None:
    set_solver(_BuiltinYesNoSolver())
    assert is_disagreement("yeah") is False


def test_is_disagreement_default_on_ambiguous() -> None:
    set_solver(_BuiltinYesNoSolver())
    assert is_disagreement("whatever", default=False) is False
    assert is_disagreement("whatever", default=True) is True


# ---------------------------------------------------------------------------
# lang forwarding
# ---------------------------------------------------------------------------

def test_lang_forwarded_to_solver() -> None:
    mock_solver = MagicMock()
    mock_solver.match_yes_or_no.return_value = True
    set_solver(mock_solver)
    parse_yes_no("oui", lang="fr-FR")
    mock_solver.match_yes_or_no.assert_called_once_with("oui", "fr-FR")
