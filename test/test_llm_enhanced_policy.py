"""Tests for LLMEnhancedPolicy."""
from unittest.mock import MagicMock
import pytest
from difficult_dialogs.arguments import Argument
from difficult_dialogs.premises import Premise
from difficult_dialogs.policy import LLMEnhancedPolicy, KnowItAllPolicy


def make_arg() -> Argument:
    arg = Argument(name="test", intro="Hello.", conclusion="Done.")
    p = Premise(name="p1")
    p.add_statement("stmt one")
    arg.add_premise(p)
    return arg


def make_enhancer(rephrase_fn=None) -> MagicMock:
    enhancer = MagicMock()
    if rephrase_fn:
        enhancer.rephrase.side_effect = rephrase_fn
    else:
        enhancer.rephrase.side_effect = lambda text, style="conversational": f"[ENHANCED] {text}"
    return enhancer


# ------------------------------------------------------------------ #
# construction
# ------------------------------------------------------------------ #

def test_wraps_inner_policy() -> None:
    arg = make_arg()
    inner = KnowItAllPolicy(arg)
    enhancer = make_enhancer()
    policy = LLMEnhancedPolicy(arg, inner, enhancer)
    assert policy._inner is inner


# ------------------------------------------------------------------ #
# start
# ------------------------------------------------------------------ #

def test_start_rephrases_intro() -> None:
    arg = make_arg()
    enhancer = make_enhancer()
    policy = LLMEnhancedPolicy(arg, KnowItAllPolicy(arg), enhancer)
    result = policy.start()
    assert result == "[ENHANCED] Hello."
    enhancer.rephrase.assert_called_once()


def test_start_records_transcript() -> None:
    arg = make_arg()
    policy = LLMEnhancedPolicy(arg, KnowItAllPolicy(arg), make_enhancer())
    policy.start()
    assert len(policy.state.transcript) == 1
    assert policy.state.transcript[0].role == "bot"


# ------------------------------------------------------------------ #
# handle_input
# ------------------------------------------------------------------ #

def test_handle_input_rephrases_response() -> None:
    arg = make_arg()
    policy = LLMEnhancedPolicy(arg, KnowItAllPolicy(arg), make_enhancer())
    policy.start()
    response = policy.handle_input("yes")
    assert response is None or response.startswith("[ENHANCED]")


def test_handle_input_records_user_turn() -> None:
    arg = make_arg()
    policy = LLMEnhancedPolicy(arg, KnowItAllPolicy(arg), make_enhancer())
    policy.start()
    policy.handle_input("yes")
    roles = [e.role for e in policy.state.transcript]
    assert "user" in roles


def test_finished_flag_propagates() -> None:
    arg = make_arg()
    policy = LLMEnhancedPolicy(arg, KnowItAllPolicy(arg), make_enhancer())
    policy.start()
    for _ in range(10):
        if policy.state.finished:
            break
        policy.handle_input("yes")
    assert policy.state.finished is True


# ------------------------------------------------------------------ #
# fallback on enhancer failure
# ------------------------------------------------------------------ #

def test_fallback_on_enhancer_exception() -> None:
    arg = make_arg()
    enhancer = MagicMock()
    enhancer.rephrase.side_effect = RuntimeError("server down")
    policy = LLMEnhancedPolicy(arg, KnowItAllPolicy(arg), enhancer)
    result = policy.start()
    # Should return original text, not raise
    assert result == "Hello."


# ------------------------------------------------------------------ #
# style forwarded
# ------------------------------------------------------------------ #

def test_style_forwarded_to_enhancer() -> None:
    arg = make_arg()
    enhancer = make_enhancer()
    policy = LLMEnhancedPolicy(arg, KnowItAllPolicy(arg), enhancer, style="formal")
    policy.start()
    _, kwargs = enhancer.rephrase.call_args
    assert kwargs.get("style") == "formal"


# ------------------------------------------------------------------ #
# end()
# ------------------------------------------------------------------ #

def test_end_rephrases_conclusion() -> None:
    arg = make_arg()
    enhancer = make_enhancer()
    policy = LLMEnhancedPolicy(arg, KnowItAllPolicy(arg), enhancer)
    result = policy.end()
    assert result == "[ENHANCED] Done."
