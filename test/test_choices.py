"""Tests for difficult_dialogs.choices module."""
import pytest
from unittest.mock import MagicMock

from difficult_dialogs.choices import (
    ChoiceOption,
    _DefaultChoiceSolver,
    _OPMChoiceSolverAdapter,
    _load_opm_solver,
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
    def test_default_solver_label(self, options: list[ChoiceOption]) -> None:
        """Label-based queries always use offline matcher first — even with OPM active."""
        result = parse_choice("A", options, "en-US")
        assert result is options[0]

    def test_custom_solver(self, options: list[ChoiceOption]) -> None:
        class AlwaysFirst:
            def match_choice(self, text: str, opts: list[ChoiceOption], lang: str) -> ChoiceOption | None:
                return opts[0] if opts else None

        result = parse_choice("anything", options, "en-US", solver=AlwaysFirst())
        assert result is options[0]

    def test_offline_solver_returns_none_on_no_match(self, options: list[ChoiceOption]) -> None:
        """The offline _DefaultChoiceSolver returns None for unrecognised input."""
        from difficult_dialogs.choices import _DefaultChoiceSolver
        solver = _DefaultChoiceSolver()
        assert solver.match_choice("zzz", options, "en-US") is None


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


# ---------------------------------------------------------------------------
# _OPMChoiceSolverAdapter — semantic fallback path
# ---------------------------------------------------------------------------

class TestOPMChoiceSolverAdapter:
    """Exercise lines 226-240: OPM select_answer semantic fallback."""

    def _options(self) -> list[ChoiceOption]:
        return [
            ChoiceOption(label="A", text="I agree completely"),
            ChoiceOption(label="B", text="I disagree", outcome="disagree"),
        ]

    def test_opm_fallback_returns_matched_option(self) -> None:
        """When offline matcher fails, OPM solver index is used."""
        mock_opm = MagicMock()
        mock_opm.select_answer.return_value = 1  # index of "I disagree"
        adapter = _OPMChoiceSolverAdapter(mock_opm)
        opts = self._options()
        # Use free-text that won't match offline labels
        result = adapter.match_choice("that's wrong", opts, "en-US")
        assert result is not None
        assert result.label == "B"
        mock_opm.select_answer.assert_called_once()

    def test_opm_fallback_invalid_index_returns_none(self) -> None:
        """OPM returns out-of-range index → None."""
        mock_opm = MagicMock()
        mock_opm.select_answer.return_value = 99
        adapter = _OPMChoiceSolverAdapter(mock_opm)
        result = adapter.match_choice("random text", self._options(), "en-US")
        assert result is None

    def test_opm_fallback_exception_returns_none(self) -> None:
        """OPM solver raises → logged warning, returns None."""
        mock_opm = MagicMock()
        mock_opm.select_answer.side_effect = RuntimeError("model crashed")
        adapter = _OPMChoiceSolverAdapter(mock_opm)
        result = adapter.match_choice("random text", self._options(), "en-US")
        assert result is None

    def test_offline_match_takes_priority(self) -> None:
        """Label match should return before OPM is called."""
        mock_opm = MagicMock()
        adapter = _OPMChoiceSolverAdapter(mock_opm)
        result = adapter.match_choice("A", self._options(), "en-US")
        assert result is not None
        assert result.label == "A"
        mock_opm.select_answer.assert_not_called()


class TestOPMLoaderEdgeCases:
    """Exercise _load_opm_solver error paths (lines 268-283)."""

    def test_loader_broken_plugin_falls_back(self, monkeypatch) -> None:
        """A plugin that raises on instantiation → fallback to default solver."""
        bad_ep = MagicMock()
        bad_ep.name = "broken-plugin"
        bad_ep.load.return_value = MagicMock(side_effect=RuntimeError("init failed"))
        monkeypatch.setattr(
            "importlib.metadata.entry_points",
            lambda group: [bad_ep],
        )
        solver = _load_opm_solver("broken-plugin")
        assert isinstance(solver, _DefaultChoiceSolver)

    def test_loader_no_plugins_returns_default(self, monkeypatch) -> None:
        monkeypatch.setattr(
            "importlib.metadata.entry_points",
            lambda group: [],
        )
        solver = _load_opm_solver(None)
        assert isinstance(solver, _DefaultChoiceSolver)
