"""Tests for choice/branching extensions to ArgumentBuilder / PremiseBuilder."""
import pytest

from difficult_dialogs.builder import ArgumentBuilder
from difficult_dialogs.choices import ChoiceOption


class TestPremiseBuilderChoices:
    def test_add_choice_auto_label(self) -> None:
        arg = (
            ArgumentBuilder("t")
            .premise("p1")
                .statement("claim")
                .choice("Yes")
                .choice("No", outcome="disagree")
                .done()
            .build()
        )
        p1 = arg.get_premise("p1")
        assert p1 is not None
        assert len(p1.choices) == 2
        assert p1.choices[0].label == "A"
        assert p1.choices[1].label == "B"
        assert p1.choices[1].outcome == "disagree"

    def test_add_choice_explicit_label(self) -> None:
        arg = (
            ArgumentBuilder("t")
            .premise("p1")
                .statement("claim")
                .choice("Option X", label="X")
                .done()
            .build()
        )
        p1 = arg.get_premise("p1")
        assert p1 is not None
        assert p1.choices[0].label == "X"

    def test_add_choice_with_next_premise(self) -> None:
        arg = (
            ArgumentBuilder("t")
            .premise("p1")
                .statement("claim")
                .choice("Jump to p2", next_premise="p2")
                .done()
            .premise("p2").statement("next").done()
            .build()
        )
        p1 = arg.get_premise("p1")
        assert p1 is not None
        assert p1.choices[0].next_premise == "p2"


class TestPremiseBuilderBranching:
    def test_on_agree(self) -> None:
        arg = (
            ArgumentBuilder("t")
            .premise("p1")
                .statement("claim")
                .on_agree("p_yes")
                .done()
            .premise("p_yes").statement("yes path").done()
            .build()
        )
        p1 = arg.get_premise("p1")
        assert p1 is not None
        assert p1.on_agree == "p_yes"
        assert arg.next_premise("p1", "agree") == "p_yes"

    def test_on_disagree(self) -> None:
        arg = (
            ArgumentBuilder("t")
            .premise("p1")
                .statement("claim")
                .on_disagree("p_no")
                .done()
            .premise("p_no").statement("no path").done()
            .build()
        )
        p1 = arg.get_premise("p1")
        assert p1 is not None
        assert p1.on_disagree == "p_no"
        assert arg.next_premise("p1", "disagree") == "p_no"


class TestPremiseBuilderBranch:
    def test_branch_sets_both_edges(self) -> None:
        arg = (
            ArgumentBuilder("t")
            .premise("p1")
                .statement("claim")
                .branch(on_agree="p_yes", on_disagree="p_no")
                .done()
            .premise("p_yes").statement("yes").done()
            .premise("p_no").statement("no").done()
            .build()
        )
        p1 = arg.get_premise("p1")
        assert p1 is not None
        assert p1.on_agree == "p_yes"
        assert p1.on_disagree == "p_no"
        assert arg.next_premise("p1", "agree") == "p_yes"
        assert arg.next_premise("p1", "disagree") == "p_no"

    def test_branch_partial_agree_only(self) -> None:
        arg = (
            ArgumentBuilder("t")
            .premise("p1")
                .statement("claim")
                .branch(on_agree="p_yes")
                .done()
            .premise("p_yes").statement("yes").done()
            .build()
        )
        p1 = arg.get_premise("p1")
        assert p1 is not None
        assert p1.on_agree == "p_yes"
        assert p1.on_disagree is None

    def test_branch_partial_disagree_only(self) -> None:
        arg = (
            ArgumentBuilder("t")
            .premise("p1")
                .statement("claim")
                .branch(on_disagree="p_no")
                .done()
            .premise("p_no").statement("no").done()
            .build()
        )
        p1 = arg.get_premise("p1")
        assert p1 is not None
        assert p1.on_agree is None
        assert p1.on_disagree == "p_no"


class TestArgumentBuilderEntryPoint:
    def test_entry_point_stored(self) -> None:
        arg = (
            ArgumentBuilder("t")
            .entry_point("p2")
            .premise("p1").statement("first").done()
            .premise("p2").statement("second").done()
            .build()
        )
        assert arg.entry_point == "p2"

    def test_entry_point_round_trip_via_dict(self) -> None:
        from difficult_dialogs.arguments import Argument
        arg = (
            ArgumentBuilder("t")
            .entry_point("p2")
            .premise("p1").statement("a").done()
            .premise("p2").statement("b").done()
            .build()
        )
        d = arg.to_dict()
        restored = Argument.from_dict(d)
        assert restored.entry_point == "p2"
