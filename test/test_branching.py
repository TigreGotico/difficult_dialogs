"""Tests for branching Argument.next_premise() graph traversal."""
import pytest

from difficult_dialogs.arguments import Argument
from difficult_dialogs.builder import ArgumentBuilder
from difficult_dialogs.premises import Premise


def _make_linear_arg() -> Argument:
    """Three premises with no explicit branching — linear by default."""
    return (
        ArgumentBuilder("linear")
        .intro("Let's begin.")
        .conclusion("Done.")
        .premise("p1").statement("Statement 1").done()
        .premise("p2").statement("Statement 2").done()
        .premise("p3").statement("Statement 3").done()
        .build()
    )


def _make_branching_arg() -> Argument:
    """p1 branches: agree→p2a, disagree→p2b; both lead to p3."""
    return (
        ArgumentBuilder("branching")
        .intro("Let's branch.")
        .conclusion("Done.")
        .premise("p1")
            .statement("Do you agree?")
            .on_agree("p2a")
            .on_disagree("p2b")
            .done()
        .premise("p2a").statement("Agreement path.").done()
        .premise("p2b").statement("Disagreement path.").done()
        .premise("p3").statement("Shared conclusion.").done()
        .build()
    )


class TestLinearFallback:
    def test_next_from_first(self) -> None:
        arg = _make_linear_arg()
        assert arg.next_premise("p1", "agree") == "p2"

    def test_next_from_second(self) -> None:
        arg = _make_linear_arg()
        assert arg.next_premise("p2", "agree") == "p3"

    def test_last_returns_none(self) -> None:
        arg = _make_linear_arg()
        assert arg.next_premise("p3", "agree") is None

    def test_disagree_follows_linear_when_no_branch(self) -> None:
        arg = _make_linear_arg()
        assert arg.next_premise("p1", "disagree") == "p2"

    def test_unknown_premise_returns_none(self) -> None:
        arg = _make_linear_arg()
        assert arg.next_premise("nonexistent", "agree") is None


class TestExplicitBranching:
    def test_agree_branch(self) -> None:
        arg = _make_branching_arg()
        assert arg.next_premise("p1", "agree") == "p2a"

    def test_disagree_branch(self) -> None:
        arg = _make_branching_arg()
        assert arg.next_premise("p1", "disagree") == "p2b"

    def test_p2a_linear_fallback_to_p2b(self) -> None:
        arg = _make_branching_arg()
        # p2a has no explicit edges; falls back to insertion-order next (p2b)
        assert arg.next_premise("p2a", "agree") == "p2b"

    def test_dangling_on_agree_returns_none(self) -> None:
        """on_agree pointing to a non-existent premise → None."""
        p = Premise(name="p1")
        p.add_statement("x")
        p.on_agree = "does_not_exist"
        arg = Argument(name="test")
        arg.add_premise(p)
        assert arg.next_premise("p1", "agree") is None


class TestChoiceNextPremise:
    def test_choice_next_premise_overrides_linear(self) -> None:
        arg = (
            ArgumentBuilder("choice_branch")
            .premise("p1")
                .statement("Pick one.")
                .choice("Go to p_alt", outcome="agree", next_premise="p_alt")
                .done()
            .premise("p2").statement("Linear next.").done()
            .premise("p_alt").statement("Alternative.").done()
            .build()
        )
        assert arg.next_premise("p1", "agree") == "p_alt"

    def test_choice_without_next_premise_falls_back(self) -> None:
        arg = (
            ArgumentBuilder("no_jump")
            .premise("p1")
                .statement("Pick one.")
                .choice("Option A", outcome="agree")  # no next_premise
                .done()
            .premise("p2").statement("Next.").done()
            .build()
        )
        # No next_premise on choice → linear fallback
        assert arg.next_premise("p1", "agree") == "p2"


class TestFileBased:
    def test_load_on_agree_file(self, tmp_path: "pytest.TempPathFactory") -> None:
        """Verify that .on_agree files are loaded from disk."""
        arg_dir = tmp_path / "test_arg"
        p1_dir = arg_dir / "p1"
        p2_dir = arg_dir / "p2"
        p1_dir.mkdir(parents=True)
        p2_dir.mkdir(parents=True)
        (arg_dir / "intro.dialog").write_text("Intro")
        (arg_dir / "conclusion.conclusion").write_text("Done")
        (p1_dir / "p1.premise").write_text("Statement one")
        (p1_dir / "p1.on_agree").write_text("p2")
        (p2_dir / "p2.premise").write_text("Statement two")

        arg = Argument.from_directory(arg_dir)
        assert arg.next_premise("p1", "agree") == "p2"

    def test_load_choices_file(self, tmp_path: "pytest.TempPathFactory") -> None:
        """Verify that .choices files are loaded from disk."""
        arg_dir = tmp_path / "choice_arg"
        p1_dir = arg_dir / "p1"
        p1_dir.mkdir(parents=True)
        (arg_dir / "intro.dialog").write_text("Intro")
        (arg_dir / "conclusion.conclusion").write_text("Done")
        (p1_dir / "p1.premise").write_text("Choose your path")
        (p1_dir / "p1.choices").write_text(
            "A) I agree -> p_yes\nB) I disagree -> p_no\n"
        )

        arg = Argument.from_directory(arg_dir)
        p1 = arg.get_premise("p1")
        assert p1 is not None
        assert len(p1.choices) == 2
        assert p1.choices[0].next_premise == "p_yes"
        assert p1.choices[1].next_premise == "p_no"


class TestSaveRoundTrip:
    def test_branching_saves_and_reloads(self, tmp_path: "pytest.TempPathFactory") -> None:
        """save() writes .on_agree/.on_disagree; reload produces same graph."""
        arg = _make_branching_arg()
        saved_path = arg.save(tmp_path / "branching")
        reloaded = Argument.from_directory(saved_path)

        assert reloaded.next_premise("p1", "agree") == "p2a"
        assert reloaded.next_premise("p1", "disagree") == "p2b"

    def test_choices_save_and_reload(self, tmp_path: "pytest.TempPathFactory") -> None:
        """save() writes .choices; reload restores all options."""
        arg = (
            ArgumentBuilder("choices_test")
            .premise("p1")
                .statement("Pick one.")
                .choice("Yes", outcome="agree", next_premise="p2")
                .choice("No", outcome="disagree")
                .done()
            .premise("p2").statement("Good.").done()
            .build()
        )
        saved_path = arg.save(tmp_path / "choices_test")
        reloaded = Argument.from_directory(saved_path)
        p1 = reloaded.get_premise("p1")
        assert p1 is not None
        assert len(p1.choices) == 2
        assert p1.choices[0].text == "Yes"
        assert p1.choices[0].next_premise == "p2"
        assert p1.choices[1].outcome == "disagree"
