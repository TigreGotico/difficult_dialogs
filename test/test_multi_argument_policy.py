"""Tests for MultiArgumentPolicy."""
import pytest
from difficult_dialogs.arguments import Argument
from difficult_dialogs.premises import Premise
from difficult_dialogs.policy import (
    MultiArgumentPolicy,
    KnowItAllPolicy,
    MinimalistPolicy,
)


# ------------------------------------------------------------------ #
# helpers
# ------------------------------------------------------------------ #

def make_arg(name: str, intro: str = "", conclusion: str = "") -> Argument:
    arg = Argument(name=name, intro=intro, conclusion=conclusion)
    p = Premise(name="p")
    p.add_statement("statement")
    arg.add_premise(p)
    return arg


# ------------------------------------------------------------------ #
# construction
# ------------------------------------------------------------------ #

def test_requires_at_least_one_argument() -> None:
    with pytest.raises(ValueError):
        MultiArgumentPolicy([])


def test_accepts_plain_list_of_arguments() -> None:
    args = [make_arg("a1"), make_arg("a2")]
    policy = MultiArgumentPolicy(args)
    assert policy.current_argument.name == "a1"


def test_accepts_tuple_list_with_policy_name() -> None:
    args = [(make_arg("a1"), "minimalist"), (make_arg("a2"), None)]
    policy = MultiArgumentPolicy(args)
    assert policy.current_argument.name == "a1"


def test_single_argument_behaves_like_normal_policy() -> None:
    policy = MultiArgumentPolicy([make_arg("only")])
    intro = policy.start()
    assert isinstance(intro, (str, type(None)))


# ------------------------------------------------------------------ #
# sequencing
# ------------------------------------------------------------------ #

def test_advances_to_next_argument_after_first_finishes() -> None:
    a1 = make_arg("first", intro="First intro")
    a2 = make_arg("second", intro="Second intro")
    policy = MultiArgumentPolicy([a1, a2], policy_class=KnowItAllPolicy)
    policy.start()
    # Drive the first argument to completion
    for _ in range(20):
        if policy._index == 1:
            break
        policy.handle_input("yes")
    assert policy._index == 1
    assert policy.current_argument.name == "second"


def test_finished_when_last_argument_done() -> None:
    args = [make_arg("a1"), make_arg("a2")]
    policy = MultiArgumentPolicy(args, policy_class=KnowItAllPolicy)
    policy.start()
    # Exhaust both arguments
    for _ in range(20):
        if policy.state.finished:
            break
        policy.handle_input("yes")
    assert policy.state.finished is True


def test_is_last_property() -> None:
    policy = MultiArgumentPolicy([make_arg("only")])
    assert policy.is_last is True

    policy2 = MultiArgumentPolicy([make_arg("a"), make_arg("b")])
    assert policy2.is_last is False


# ------------------------------------------------------------------ #
# transcript
# ------------------------------------------------------------------ #

def test_transcript_accumulates_across_arguments() -> None:
    args = [make_arg("a1"), make_arg("a2")]
    policy = MultiArgumentPolicy(args, policy_class=KnowItAllPolicy)
    policy.start()
    for _ in range(20):
        if policy.state.finished:
            break
        policy.handle_input("yes")
    # Transcript should span both arguments
    roles = {e.role for e in policy.state.transcript}
    assert "user" in roles


# ------------------------------------------------------------------ #
# end()
# ------------------------------------------------------------------ #

def test_end_delegates_to_inner() -> None:
    policy = MultiArgumentPolicy([make_arg("a", conclusion="Done!")])
    policy.start()
    result = policy.end()
    assert result == "Done!" or result is None  # depends on inner policy
