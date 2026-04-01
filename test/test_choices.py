"""Tests for difficult_dialogs.choices module."""
import pytest

from difficult_dialogs.choices import (
    ChoiceOption,
    _DefaultChoiceSolver,
    parse_choice,
    parse_choices_file,
)


# ---------------------------------------------------------------------------
# ChoiceOption
# ---------------------------------------------------------------------------

class TestChoiceOption:
    def test_defaults(self) -> None:
        opt = ChoiceOption(label="A", text="I agree")
        assert opt.outcome == "agree"
        assert opt.next_premise is None

    def test_to_dict_round_trip(self) -> None:
        opt = ChoiceOption(label="B", text="I disagree", outcome="disagree", next_premise="p2")
        d = opt.to_dict()
        restored = ChoiceOption.from_dict(d)
        assert restored.label == opt.label
        assert restored.text == opt.text
        assert restored.outcome == opt.outcome
        assert restored.next_premise == opt.next_premise

    def test_from_dict_empty_next_premise(self) -> None:
        d = {"label": "A", "text": "ok", "outcome": "agree", "next_premise": None}
        opt = ChoiceOption.from_dict(d)
        assert opt.next_premise is None

    def test_from_dict_empty_string_next_premise(self) -> None:
        d = {"label": "A", "text": "ok", "outcome": "agree", "next_premise": ""}
        opt = ChoiceOption.from_dict(d)
        assert opt.next_premise is None


# ---------------------------------------------------------------------------
# _DefaultChoiceSolver
# ---------------------------------------------------------------------------

@pytest.fixture
def options() -> list[ChoiceOption]:
    return [
        ChoiceOption("A", "I agree", "agree"),
        ChoiceOption("B", "I disagree", "disagree"),
        ChoiceOption("C", "I need clarification", "clarify"),
    ]


@pytest.fixture
def solver() -> _DefaultChoiceSolver:
    return _DefaultChoiceSolver()


class TestDefaultChoiceSolver:
    def test_exact_label(self, solver: _DefaultChoiceSolver, options: list[ChoiceOption]) -> None:
        assert solver.match_choice("A", options, "en-US") is options[0]
        assert solver.match_choice("b", options, "en-US") is options[1]
        assert solver.match_choice("C", options, "en-US") is options[2]

    def test_label_with_punctuation(self, solver: _DefaultChoiceSolver, options: list[ChoiceOption]) -> None:
        assert solver.match_choice("a)", options, "en-US") is options[0]
        assert solver.match_choice("B.", options, "en-US") is options[1]
        assert solver.match_choice("c:", options, "en-US") is options[2]
        assert solver.match_choice("A ", options, "en-US") is options[0]

    def test_integer_index(self, solver: _DefaultChoiceSolver, options: list[ChoiceOption]) -> None:
        assert solver.match_choice("1", options, "en-US") is options[0]
        assert solver.match_choice("2", options, "en-US") is options[1]
        assert solver.match_choice("3", options, "en-US") is options[2]

    def test_integer_index_out_of_range(self, solver: _DefaultChoiceSolver, options: list[ChoiceOption]) -> None:
        assert solver.match_choice("0", options, "en-US") is None
        assert solver.match_choice("4", options, "en-US") is None

    def test_text_prefix(self, solver: _DefaultChoiceSolver, options: list[ChoiceOption]) -> None:
        assert solver.match_choice("I agree", options, "en-US") is options[0]
        assert solver.match_choice("I dis", options, "en-US") is options[1]
        assert solver.match_choice("I need", options, "en-US") is options[2]

    def test_short_prefix_ignored(self, solver: _DefaultChoiceSolver, options: list[ChoiceOption]) -> None:
        # < 3 chars: no prefix match
        assert solver.match_choice("I", options, "en-US") is None

    def test_no_match(self, solver: _DefaultChoiceSolver, options: list[ChoiceOption]) -> None:
        assert solver.match_choice("xyz", options, "en-US") is None


# ---------------------------------------------------------------------------
# parse_choice (public API)
# ---------------------------------------------------------------------------

class TestParseChoice:
    def test_default_solver(self, options: list[ChoiceOption]) -> None:
        result = parse_choice("A", options, "en-US")
        assert result is options[0]

    def test_custom_solver(self, options: list[ChoiceOption]) -> None:
        class AlwaysFirst:
            def match_choice(self, text: str, opts: list[ChoiceOption], lang: str) -> ChoiceOption | None:
                return opts[0] if opts else None

        result = parse_choice("anything", options, "en-US", solver=AlwaysFirst())
        assert result is options[0]

    def test_returns_none_on_no_match(self, options: list[ChoiceOption]) -> None:
        assert parse_choice("zzz", options, "en-US") is None


# ---------------------------------------------------------------------------
# parse_choices_file
# ---------------------------------------------------------------------------

class TestParseChoicesFile:
    def test_full_format(self) -> None:
        raw = (
            "A) I agree completely -> next_premise\n"
            "B) I agree with reservations\n"
            "C) I disagree [disagree]\n"
            "D) I need more context [clarify]\n"
        )
        opts = parse_choices_file(raw)
        assert len(opts) == 4
        assert opts[0].label == "A"
        assert opts[0].text == "I agree completely"
        assert opts[0].next_premise == "next_premise"
        assert opts[0].outcome == "agree"  # positional default
        assert opts[1].label == "B"
        assert opts[1].next_premise is None
        assert opts[2].outcome == "disagree"
        assert opts[3].outcome == "clarify"

    def test_blank_lines_and_comments_ignored(self) -> None:
        raw = "\n# comment\nA) option one\n\nB) option two\n"
        opts = parse_choices_file(raw)
        assert len(opts) == 2

    def test_auto_label_when_no_paren(self) -> None:
        raw = "yes\nno\nmaybe"
        opts = parse_choices_file(raw)
        assert opts[0].label == "A"
        assert opts[1].label == "B"
        assert opts[2].label == "C"
        assert opts[0].text == "yes"

    def test_arrow_and_bracket_combined(self) -> None:
        raw = "A) option [disagree] -> target_p\n"
        opts = parse_choices_file(raw)
        # bracket is parsed before arrow check — but arrow is parsed first in code
        # order: strip arrow, then strip bracket
        assert opts[0].next_premise == "target_p"
        assert opts[0].outcome == "disagree"

    def test_empty_file(self) -> None:
        assert parse_choices_file("") == []
