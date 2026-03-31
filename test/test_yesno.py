"""Tests for difficult_dialogs.yesno fuzzy yes/no detection."""
import pytest
from difficult_dialogs.yesno import parse_yes_no, is_agreement, is_disagreement


# ---------------------------------------------------------------------------
# parse_yes_no — strong yes
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
def test_strong_yes(text: str) -> None:
    assert parse_yes_no(text) is True


# ---------------------------------------------------------------------------
# parse_yes_no — strong no
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
def test_strong_no(text: str) -> None:
    assert parse_yes_no(text) is False


# ---------------------------------------------------------------------------
# parse_yes_no — neutral yes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "sure", "certainly", "definitely",
    "of course", "fine", "alright",
])
def test_neutral_yes(text: str) -> None:
    assert parse_yes_no(text) is True


# ---------------------------------------------------------------------------
# parse_yes_no — neutral no
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "that's wrong", "that seems mistaken",
    "that's a lie",
])
def test_neutral_no(text: str) -> None:
    assert parse_yes_no(text) is False


# ---------------------------------------------------------------------------
# parse_yes_no — ambiguous / neutral
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "I don't know",
    "maybe",
    "hmm",
    "",
    "what do you mean",
])
def test_ambiguous_returns_none(text: str) -> None:
    assert parse_yes_no(text) is None


# ---------------------------------------------------------------------------
# parse_yes_no — last word wins (mind change)
# ---------------------------------------------------------------------------

def test_yes_then_no_returns_no() -> None:
    assert parse_yes_no("yes wait no") is False


def test_no_then_yes_returns_yes() -> None:
    assert parse_yes_no("no actually yes") is True


# ---------------------------------------------------------------------------
# parse_yes_no — double negative
# ---------------------------------------------------------------------------

def test_double_negative_not_wrong_is_yes() -> None:
    # "not wrong" should resolve to True
    assert parse_yes_no("that's not wrong") is True


# ---------------------------------------------------------------------------
# is_agreement / is_disagreement helpers
# ---------------------------------------------------------------------------

def test_is_agreement_true_on_yes() -> None:
    assert is_agreement("yes") is True


def test_is_agreement_false_on_no() -> None:
    assert is_agreement("no") is False


def test_is_agreement_default_on_ambiguous() -> None:
    assert is_agreement("hmm", default=True) is True
    assert is_agreement("hmm", default=False) is False


def test_is_disagreement_true_on_no() -> None:
    assert is_disagreement("nope") is True


def test_is_disagreement_false_on_yes() -> None:
    assert is_disagreement("yeah") is False


def test_is_disagreement_default_on_ambiguous() -> None:
    assert is_disagreement("whatever", default=False) is False
    assert is_disagreement("whatever", default=True) is True
