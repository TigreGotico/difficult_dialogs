"""Tests for MultiChoicePolicy."""
import pytest

from difficult_dialogs.builder import ArgumentBuilder
from difficult_dialogs.policy import MultiChoicePolicy


def _make_arg_with_choices():
    """Argument with two premises: p1 has choices, p2 does not."""
    return (
        ArgumentBuilder("test")
        .intro("Hello.")
        .conclusion("Goodbye.")
        .premise("p1")
            .statement("Do you agree?")
            .choice("Yes", outcome="agree", next_premise="p2")
            .choice("No", outcome="disagree")
            .choice("Explain more", outcome="clarify")
            .done()
        .premise("p2")
            .statement("Great progress.")
            .support("Here is why it matters.")
            .done()
        .build()
    )


def _make_branching_arg():
    """p1 branches: agree→p2a, disagree→p2b."""
    return (
        ArgumentBuilder("branching")
        .intro("Start.")
        .conclusion("End.")
        .premise("p1")
            .statement("First question.")
            .on_agree("p2a")
            .on_disagree("p2b")
            .done()
        .premise("p2a").statement("Agreement path.").done()
        .premise("p2b").statement("Disagreement path.").done()
        .build()
    )


class TestMultiChoicePolicyStart:
    def test_start_returns_intro_and_first_statement(self) -> None:
        arg = _make_arg_with_choices()
        policy = MultiChoicePolicy(arg)
        text = policy.start()
        assert "Hello." in text
        assert "Do you agree?" in text
        # Choices should be presented
        assert "A)" in text
        assert "B)" in text

    def test_start_no_choices(self) -> None:
        from difficult_dialogs.builder import ArgumentBuilder
        arg = (
            ArgumentBuilder("simple")
            .intro("Hi.")
            .conclusion("Bye.")
            .premise("p1").statement("A claim.").done()
            .build()
        )
        policy = MultiChoicePolicy(arg)
        text = policy.start()
        assert "Hi." in text
        assert "A claim." in text
        # No choices menu
        assert "A)" not in text


class TestMultiChoicePolicyHandleInput:
    def test_select_by_label_advances(self) -> None:
        arg = _make_arg_with_choices()
        policy = MultiChoicePolicy(arg)
        policy.start()
        response = policy.handle_input("A")
        assert response is not None
        assert "Great progress." in response

    def test_select_by_index_advances(self) -> None:
        arg = _make_arg_with_choices()
        policy = MultiChoicePolicy(arg)
        policy.start()
        response = policy.handle_input("1")  # option 1 = A = agree
        assert response is not None
        assert "Great progress." in response

    def test_disagree_gives_support(self) -> None:
        arg = _make_arg_with_choices()
        policy = MultiChoicePolicy(arg)
        policy.start()
        response = policy.handle_input("B")  # disagree
        assert response is not None
        # Should offer support or advance
        # (p1 has no .support, so it should advance)
        assert "Great progress." in response

    def test_invalid_choice_re_presents(self) -> None:
        """When the solver returns None, the bot re-presents the choices."""
        from difficult_dialogs.choices import _DefaultChoiceSolver
        arg = _make_arg_with_choices()
        # Use offline solver so "zzz" returns None (triggering re-prompt)
        policy = MultiChoicePolicy(arg, choice_solver=_DefaultChoiceSolver())
        policy.start()
        response = policy.handle_input("zzz")
        assert response is not None
        assert "Please choose" in response

    def test_clarify_returns_context(self) -> None:
        arg = (
            ArgumentBuilder("ctx")
            .intro("Hi.")
            .conclusion("Bye.")
            .premise("p1")
                .statement("A claim.")
                .why("Because science.")
                .choice("Clarify", outcome="clarify")
                .done()
            .build()
        )
        policy = MultiChoicePolicy(arg)
        policy.start()
        response = policy.handle_input("A")  # only choice: clarify
        assert response is not None
        assert "science" in response

    def test_yes_no_fallback_when_no_choices(self) -> None:
        from difficult_dialogs.builder import ArgumentBuilder
        arg = (
            ArgumentBuilder("yesno")
            .intro("Hi.")
            .conclusion("Bye.")
            .premise("p1").statement("Agree?").done()
            .premise("p2").statement("Next.").done()
            .build()
        )
        policy = MultiChoicePolicy(arg)
        policy.start()
        response = policy.handle_input("yes")
        assert response is not None
        assert "Next." in response

    def test_branching_via_on_agree(self) -> None:
        arg = _make_branching_arg()
        policy = MultiChoicePolicy(arg)
        policy.start()
        response = policy.handle_input("yes")
        assert response is not None
        assert "Agreement path." in response

    def test_branching_via_on_disagree(self) -> None:
        arg = _make_branching_arg()
        policy = MultiChoicePolicy(arg)
        policy.start()
        response = policy.handle_input("no")
        assert response is not None
        assert "Disagreement path." in response

    def test_end_reached_returns_conclusion(self) -> None:
        arg = (
            ArgumentBuilder("short")
            .intro("Start.")
            .conclusion("The end.")
            .premise("p1").statement("Only claim.").done()
            .build()
        )
        policy = MultiChoicePolicy(arg)
        policy.start()
        response = policy.handle_input("yes")
        assert response == "The end."
        assert policy.state.finished

    def test_registered_in_policy_registry(self) -> None:
        from difficult_dialogs.policy import POLICY_REGISTRY
        assert "multichoice" in POLICY_REGISTRY
        assert POLICY_REGISTRY["multichoice"] is MultiChoicePolicy

    def test_choice_jumps_to_premise_that_has_choices(self) -> None:
        """Line 1604-1605: jump target also has choices → they are presented."""
        arg = (
            ArgumentBuilder("chained")
            .intro("Go.")
            .conclusion("Done.")
            .premise("p1")
                .statement("Step 1.")
                .choice("Next", outcome="agree", next_premise="p2")
                .done()
            .premise("p2")
                .statement("Step 2.")
                .choice("Finish", outcome="agree", next_premise=None)
                .done()
            .build()
        )
        policy = MultiChoicePolicy(arg)
        policy.start()
        response = policy.handle_input("A")  # selects choice → jumps to p2
        assert response is not None
        assert "Step 2." in response
        assert "Finish" in response  # p2's choices are shown

    def test_choice_jumps_to_empty_premise_ends_dialog(self) -> None:
        """Line 1607: jump target has statements already spoken → end()."""
        from difficult_dialogs.premises import Premise
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.choices import ChoiceOption
        arg = Argument(name="edge", intro="Hi.", conclusion="The end.")
        p1 = Premise(name="p1")
        p1.add_statement("Question.")
        p1.choices.append(ChoiceOption("A", "Jump", "agree", next_premise="p2"))
        p2 = Premise(name="p2")
        p2.add_statement("Already spoken.")
        arg.add_premise(p1)
        arg.add_premise(p2)
        policy = MultiChoicePolicy(arg)
        policy.start()
        # Pre-mark p2's statement as spoken so get_next_statement returns None
        policy.state.spoken_statements.add("Already spoken.")
        response = policy.handle_input("A")
        assert response == "The end."
        assert policy.state.finished

    def test_choice_agree_with_no_more_premises_ends(self) -> None:
        """Line 1619: agree choice, no more premises → end."""
        arg = (
            ArgumentBuilder("single")
            .intro("Hi.")
            .conclusion("Bye.")
            .premise("p1")
                .statement("Only.")
                .choice("Yes", outcome="agree")
                .done()
            .build()
        )
        policy = MultiChoicePolicy(arg)
        policy.start()
        response = policy.handle_input("A")
        assert response == "Bye."
        assert policy.state.finished

    def test_choice_disagree_returns_support(self) -> None:
        """Line 1625: disagree choice where support exists."""
        arg = (
            ArgumentBuilder("with_support")
            .intro("Hi.")
            .conclusion("Bye.")
            .premise("p1")
                .statement("Claim.")
                .support("Here is why.")
                .choice("No", outcome="disagree")
                .done()
            .build()
        )
        policy = MultiChoicePolicy(arg)
        policy.start()
        response = policy.handle_input("A")  # disagree
        assert response == "Here is why."

    def test_choice_disagree_advances_to_premise_with_choices(self) -> None:
        """Lines 1632-1633: disagree choice, next premise has choices."""
        arg = (
            ArgumentBuilder("disagree_choices")
            .intro("Hi.")
            .conclusion("Bye.")
            .premise("p1")
                .statement("Q1.")
                .choice("Disagree", outcome="disagree")
                .done()
            .premise("p2")
                .statement("Q2.")
                .choice("Yes", outcome="agree")
                .done()
            .build()
        )
        policy = MultiChoicePolicy(arg)
        policy.start()
        response = policy.handle_input("A")  # disagree, no support
        assert response is not None
        assert "Q2." in response
        assert "Yes" in response  # p2 choices shown

    def test_choice_disagree_no_more_premises_ends(self) -> None:
        """Line 1635: disagree choice, no more premises → end."""
        arg = (
            ArgumentBuilder("disagree_end")
            .intro("Hi.")
            .conclusion("Bye.")
            .premise("p1")
                .statement("Only.")
                .choice("No", outcome="disagree")
                .done()
            .build()
        )
        policy = MultiChoicePolicy(arg)
        policy.start()
        response = policy.handle_input("A")
        assert response == "Bye."

    def test_clarify_no_context_returns_generic_message(self) -> None:
        """Line 1644: clarify with no why/what/how context."""
        arg = (
            ArgumentBuilder("no_ctx")
            .intro("Hi.")
            .conclusion("Bye.")
            .premise("p1")
                .statement("Claim.")
                .choice("Clarify", outcome="clarify")
                .done()
            .build()
        )
        policy = MultiChoicePolicy(arg)
        policy.start()
        response = policy.handle_input("A")
        assert response is not None
        assert "clarified" in response.lower()

    def test_yesno_fallback_five_w(self) -> None:
        """Line 1649: Five-W question triggers contextual answer."""
        arg = (
            ArgumentBuilder("fw")
            .intro("Hi.")
            .conclusion("Bye.")
            .premise("p1")
                .statement("Claim.")
                .why("Because physics.")
                .done()
            .premise("p2").statement("Next.").done()
            .build()
        )
        policy = MultiChoicePolicy(arg)
        policy.start()
        response = policy.handle_input("why is this true")
        assert response == "Because physics."

    def test_yesno_agree_advances_to_premise_with_choices(self) -> None:
        """Lines 1658-1659: yes/no agree path, next premise has choices."""
        arg = (
            ArgumentBuilder("agree_choices")
            .intro("Hi.")
            .conclusion("Bye.")
            .premise("p1").statement("Q1.").done()
            .premise("p2")
                .statement("Q2.")
                .choice("Finish", outcome="agree")
                .done()
            .build()
        )
        policy = MultiChoicePolicy(arg)
        policy.start()
        response = policy.handle_input("yes")
        assert response is not None
        assert "Q2." in response
        assert "Finish" in response

    def test_yesno_disagree_returns_support(self) -> None:
        """Line 1667: yes/no disagree path where support exists."""
        arg = (
            ArgumentBuilder("yesno_support")
            .intro("Hi.")
            .conclusion("Bye.")
            .premise("p1")
                .statement("Claim.")
                .support("Evidence.")
                .done()
            .premise("p2").statement("Next.").done()
            .build()
        )
        policy = MultiChoicePolicy(arg)
        policy.start()
        response = policy.handle_input("no")
        assert response == "Evidence."

    def test_yesno_disagree_advances_to_premise_with_choices(self) -> None:
        """Lines 1674-1675: yes/no disagree, next premise has choices."""
        arg = (
            ArgumentBuilder("disagree_yesno_choices")
            .intro("Hi.")
            .conclusion("Bye.")
            .premise("p1").statement("Q1.").done()
            .premise("p2")
                .statement("Q2.")
                .choice("Opt", outcome="agree")
                .done()
            .build()
        )
        policy = MultiChoicePolicy(arg)
        policy.start()
        response = policy.handle_input("no")
        assert response is not None
        assert "Q2." in response
        assert "Opt" in response

    def test_yesno_disagree_no_more_premises_ends(self) -> None:
        """Line 1677: yes/no disagree, no more premises → end."""
        arg = (
            ArgumentBuilder("only")
            .intro("Hi.")
            .conclusion("Bye.")
            .premise("p1").statement("Only.").done()
            .build()
        )
        policy = MultiChoicePolicy(arg)
        policy.start()
        response = policy.handle_input("no")
        assert response == "Bye."

    def test_ambiguous_input_advances_with_choices(self) -> None:
        """Lines 1684-1686: ambiguous input, next premise has choices."""
        arg = (
            ArgumentBuilder("ambig")
            .intro("Hi.")
            .conclusion("Bye.")
            .premise("p1").statement("Q1.").done()
            .premise("p2")
                .statement("Q2.")
                .choice("Go", outcome="agree")
                .done()
            .build()
        )
        policy = MultiChoicePolicy(arg)
        policy.start()  # presents p1
        # Ambiguous reply — no pending choices, should advance to p2 (which has choices)
        response = policy.handle_input("hmm")
        assert response is not None
        assert "Q2." in response
        assert "Go" in response

    def test_ambiguous_input_no_more_premises_ends(self) -> None:
        """Line 1688: ambiguous input, no more premises → end."""
        arg = (
            ArgumentBuilder("ambig_end")
            .intro("Hi.")
            .conclusion("Bye.")
            .premise("p1").statement("Only.").done()
            .build()
        )
        policy = MultiChoicePolicy(arg)
        policy.start()
        # Mark everything as spoken so _get_next_statement returns None
        policy.state.spoken_statements.add("Only.")
        response = policy.handle_input("hmm")
        assert response == "Bye."

    def test_start_empty_argument_returns_intro(self) -> None:
        """Line 1705: start() when no premises exist."""
        from difficult_dialogs.arguments import Argument
        arg = Argument(name="empty", intro="Just intro.", conclusion="Done.")
        policy = MultiChoicePolicy(arg)
        text = policy.start()
        assert text == "Just intro."

    def test_choice_agree_no_next_premise_advances_to_premise_with_choices(self) -> None:
        """Lines 1613-1618: agree choice (no explicit next_premise), next premise has choices."""
        arg = (
            ArgumentBuilder("agree_chain")
            .intro("Hi.")
            .conclusion("Bye.")
            .premise("p1")
                .statement("Q1.")
                .choice("Yes", outcome="agree")  # no next_premise — uses linear order
                .done()
            .premise("p2")
                .statement("Q2.")
                .choice("Finish", outcome="agree")
                .done()
            .build()
        )
        policy = MultiChoicePolicy(arg)
        policy.start()  # presents Q1 with choices
        response = policy.handle_input("A")  # agree, no explicit jump
        assert response is not None
        assert "Q2." in response
        assert "Finish" in response  # p2 choices presented

    def test_skip_choice_advances(self) -> None:
        """Lines 1609-1618: 'skip' outcome treated same as 'agree'."""
        arg = (
            ArgumentBuilder("skip_test")
            .intro("Hi.")
            .conclusion("Bye.")
            .premise("p1")
                .statement("Q1.")
                .choice("Skip", outcome="skip")
                .done()
            .premise("p2").statement("Q2.").done()
            .build()
        )
        policy = MultiChoicePolicy(arg)
        policy.start()
        response = policy.handle_input("A")
        assert response is not None
        assert "Q2." in response

    def test_ambiguous_no_choices_fallback_advances(self) -> None:
        """Lines 1680-1688: ambiguous input, no choices on current premise, no pending."""
        arg = (
            ArgumentBuilder("ambig2")
            .intro("Hi.")
            .conclusion("Bye.")
            .premise("p1").statement("Q1.").done()
            .premise("p2").statement("Q2.").done()
            .build()
        )
        policy = MultiChoicePolicy(arg)
        policy.start()  # presents Q1, no choices
        # ambiguous input — no pending choices, no is_agreement/is_disagreement match
        response = policy.handle_input("perhaps")
        assert response is not None
        # Should advance to p2
        assert "Q2." in response
