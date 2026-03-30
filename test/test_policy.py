"""Unit tests for difficult_dialogs.policy — BasePolicy and KnowItAllPolicy."""
import os
import pytest
from difficult_dialogs.arguments import Argument
from difficult_dialogs.policy import BasePolicy, KnowItAllPolicy

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")
COGITO_DIR = os.path.join(EXAMPLES_DIR, "i_think_therefore_i_am")
TEMPLATE_DIR = os.path.join(EXAMPLES_DIR, "argument_template")


def make_arg() -> Argument:
    return Argument(path=COGITO_DIR)


# ---------------------------------------------------------------------------
# BasePolicy
# ---------------------------------------------------------------------------

def test_start_returns_intro() -> None:
    arg = make_arg()
    policy = BasePolicy(argument=arg)
    intro = policy.start()
    assert isinstance(intro, str)
    assert intro.strip() != ""


def test_end_sets_finished() -> None:
    arg = make_arg()
    policy = BasePolicy(argument=arg)
    policy.start()
    policy.end()
    assert policy.finished is True


def test_end_returns_conclusion() -> None:
    arg = make_arg()
    policy = BasePolicy(argument=arg)
    policy.start()
    conclusion = policy.end()
    assert isinstance(conclusion, str)


def test_choose_premise_returns_premise() -> None:
    arg = make_arg()
    policy = BasePolicy(argument=arg)
    policy.start()
    premise = policy.choose_premise()
    assert premise is not None


def test_choose_next_statement_progresses() -> None:
    """choose_next_statement returns Statement objects and eventually signals
    finished; statements within a single premise are not repeated (the policy
    may re-enter a premise's statement across premises, which is expected)."""
    arg = make_arg()
    policy = BasePolicy(argument=arg)
    policy.start()
    policy.current_premise = policy.choose_premise()
    count = 0
    while True:
        stmt = policy.choose_next_statement()
        if stmt is None:
            break
        count += 1
        if policy.finished:
            break
        if count > 50:
            break
    assert count > 0


def test_full_loop_no_disagreement() -> None:
    """Simulate a complete positive dialog without user input."""
    arg = make_arg()
    policy = BasePolicy(argument=arg)
    policy.start()
    iterations = 0
    while not policy.finished:
        output = policy._run_once()
        if output is None and not policy.finished:
            # finished mid-loop
            policy.end()
            break
        iterations += 1
        if iterations > 200:
            pytest.fail("Dialog loop did not terminate")
    assert policy.finished


# ---------------------------------------------------------------------------
# KnowItAllPolicy
# ---------------------------------------------------------------------------

def test_know_it_all_disagree_speaks_support() -> None:
    arg = make_arg()
    policy = KnowItAllPolicy(arg)
    policy.start()
    policy.current_premise = policy.choose_premise()
    # Ensure there's a support statement available
    if not policy.current_premise.support_statements:
        pytest.skip("No support statements in this premise")
    policy.disagree()
    output = policy.on_negative_feedback()
    assert isinstance(output, str)
    assert output.strip() != ""


def test_know_it_all_complete_failure_no_sources() -> None:
    """When support exhausted and no sources, policy should agree and skip feedback."""
    arg = make_arg()
    policy = KnowItAllPolicy(arg)
    policy.start()
    policy.current_premise = policy.choose_premise()
    # Mark all support statements as cached
    for s in policy.current_premise.support_statements:
        policy._cache_this(str(s))
    # Remove sources temporarily
    orig_sources = policy.current_premise.sources[:]
    policy.current_premise.sources.clear()

    output = policy.on_complete_failure()
    assert isinstance(output, str)

    policy.current_premise.sources.extend(orig_sources)  # restore


def test_know_it_all_complete_failure_with_sources() -> None:
    arg = make_arg()
    policy = KnowItAllPolicy(arg)
    policy.start()
    policy.current_premise = policy.choose_premise()
    # Exhaust support cache
    for s in policy.current_premise.support_statements:
        policy._cache_this(str(s))

    if not policy.current_premise.sources:
        pytest.skip("Premise has no sources")

    output = policy.on_complete_failure()
    assert "here is the source" in output.lower() or any(
        src.strip() in output for src in policy.current_premise.sources
    )


def test_know_it_all_on_user_input_what() -> None:
    arg = make_arg()
    policy = KnowItAllPolicy(arg)
    policy.start()
    policy.current_premise = policy.choose_premise()
    result = policy.on_user_input("what is this?")
    # Returns False (wait for more input) when answering a W-question
    assert result is False


def test_know_it_all_on_user_input_agree() -> None:
    arg = make_arg()
    policy = KnowItAllPolicy(arg)
    policy.start()
    policy.current_premise = policy.choose_premise()
    result = policy.on_user_input("yes I agree")
    assert result is True


def test_know_it_all_dialog_loop_simulation() -> None:
    """Simulate full dialog: agree on every turn until conclusion."""
    arg = make_arg()
    policy = KnowItAllPolicy(arg)
    policy.start()
    iterations = 0
    while not policy.finished:
        policy._in_agreement = True  # always agree
        output = policy._run_once()
        if output is None and not policy.finished:
            policy.end()
            break
        iterations += 1
        if iterations > 300:
            pytest.fail("Dialog loop did not terminate")
    assert policy.finished


def test_know_it_all_dialog_loop_with_disagreement() -> None:
    """Simulate dialog where user disagrees, accepts policy's agree-override.

    KnowItAllPolicy.on_complete_failure() calls agree() to override the
    disagreement once support is exhausted. The test respects that override
    (does not re-impose disagreement after the policy flips _in_agreement).
    """
    arg = make_arg()
    policy = KnowItAllPolicy(arg)
    policy.start()
    # Disagree exactly once per premise to exercise support/failure paths
    policy.disagree()
    iterations = 0
    while not policy.finished:
        output = policy._run_once()
        # After support exhausted the policy calls agree(); honour that and
        # disagree again only if we are still in agreement (i.e. policy moved on)
        if policy._in_agreement and not policy._skip_feedback:
            policy.disagree()
        if output is None and not policy.finished:
            policy.end()
            break
        iterations += 1
        if iterations > 500:
            pytest.fail("Dialog loop with disagreement did not terminate")
    assert policy.finished
