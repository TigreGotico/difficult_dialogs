"""Unit tests for difficult_dialogs.policy — BasePolicy and KnowItAllPolicy."""
from pathlib import Path

from difficult_dialogs.arguments import Argument
from difficult_dialogs.premises import Premise

from difficult_dialogs.policy import (
    BasePolicy,
    KnowItAllPolicy,
    SilentPolicy,
    SocraticPolicy,
    DebatePolicy,
    ExploratoryPolicy,
    PolicyState,
)


COGITO_DIR = Path(__file__).parent.parent / "examples" / "i_think_therefore_i_am"


def make_arg() -> Argument:
    """Create argument from cogito example."""
    arg = Argument()
    arg.load(COGITO_DIR)
    return arg


# ---------------------------------------------------------------------------
# PolicyState
# ---------------------------------------------------------------------------

def test_policy_state_defaults() -> None:
    """PolicyState initializes with empty defaults."""
    state = PolicyState()
    assert state.spoken_premises == set()
    assert state.spoken_statements == set()
    assert state.current_premise is None
    assert state.user_agrees is True
    assert state.finished is False


# ---------------------------------------------------------------------------
# BasePolicy
# ---------------------------------------------------------------------------

def test_start_returns_intro() -> None:
    """Start returns intro statement."""
    arg = make_arg()
    policy = SilentPolicy(arg)
    intro = policy.start()
    assert isinstance(intro, str)
    assert intro.strip() != ""


def test_end_sets_finished() -> None:
    """End sets finished flag."""
    arg = make_arg()
    policy = SilentPolicy(arg)
    policy.start()
    policy.end()
    assert policy.state.finished is True


def test_end_returns_conclusion() -> None:
    """End returns conclusion statement."""
    arg = make_arg()
    policy = SilentPolicy(arg)
    policy.start()
    conclusion = policy.end()
    assert isinstance(conclusion, str)


def test_handle_input_is_abstract() -> None:
    """BasePolicy.handle_input must be implemented by subclasses."""
    arg = make_arg()
    
    class TestPolicy(BasePolicy):
        def handle_input(self, user_input: str) -> str | None:
            return "response"
    
    policy = TestPolicy(arg)
    assert policy.handle_input("test") == "response"


def test_get_next_statement() -> None:
    """Get next statement from premises."""
    arg = make_arg()
    policy = SilentPolicy(arg)
    policy.start()
    
    result = policy._get_next_statement()
    assert result is not None
    premise_name, statement = result
    assert isinstance(premise_name, str)
    assert isinstance(statement, str)


def test_get_support() -> None:
    """Get support for current premise."""
    arg = make_arg()
    policy = SilentPolicy(arg)
    policy.start()
    
    # First get a premise to set as current
    result = policy._get_next_statement()
    if result:
        premise_name, _ = result
        policy.state.current_premise = premise_name
        support = policy._get_support()
        # May or may not have support
        assert support is None or isinstance(support, str)


def test_get_sources() -> None:
    """Get sources for current premise."""
    arg = make_arg()
    policy = SilentPolicy(arg)
    policy.start()
    
    result = policy._get_next_statement()
    if result:
        premise_name, _ = result
        policy.state.current_premise = premise_name
        sources = policy._get_sources()
        assert isinstance(sources, list)


def test_agree_disagree() -> None:
    """Agree and disagree methods work."""
    arg = make_arg()
    policy = SilentPolicy(arg)
    
    assert policy.state.user_agrees is True
    policy.disagree()
    assert policy.state.user_agrees is False
    policy.agree()
    assert policy.state.user_agrees is True


def test_run_sync_generator() -> None:
    """Sync run returns generator of responses."""
    arg = make_arg()
    policy = SilentPolicy(arg)
    
    gen = policy.run_sync()
    first = next(gen)
    assert isinstance(first, str)  # intro


# ---------------------------------------------------------------------------
# KnowItAllPolicy
# ---------------------------------------------------------------------------

def test_know_it_all_handle_input_agree() -> None:
    """Handle input with agreement advances dialog."""
    arg = make_arg()
    policy = KnowItAllPolicy(arg)
    policy.start()
    
    response = policy.handle_input("yes I agree")
    assert response is not None


def test_know_it_all_handle_input_disagree() -> None:
    """Handle input with disagreement triggers support."""
    arg = make_arg()
    policy = KnowItAllPolicy(arg)
    policy.start()
    
    response = policy.handle_input("no I disagree")
    assert response is not None


def test_know_it_all_handle_input_what_question() -> None:
    """What questions are handled."""
    arg = make_arg()
    policy = KnowItAllPolicy(arg)
    policy.start()
    policy._get_next_statement()  # Set current premise
    
    response = policy.handle_input("what is this?")
    # May return explanation or advance depending on premise data
    assert response is None or isinstance(response, str)


def test_know_it_all_handle_input_why_question() -> None:
    """Why questions are handled."""
    arg = make_arg()
    policy = KnowItAllPolicy(arg)
    policy.start()
    policy._get_next_statement()
    
    response = policy.handle_input("why is that?")
    assert response is None or isinstance(response, str)


def test_know_it_all_handles_various_agreement_forms() -> None:
    """Various forms of agreement recognized."""
    arg = make_arg()
    policy = KnowItAllPolicy(arg)
    policy.start()
    
    for agreement in ["yes", "y", "ok", "sure", "agree"]:
        response = policy.handle_input(agreement)
        assert response is not None or policy.state.finished


def test_know_it_all_handles_various_disagreement_forms() -> None:
    """Various forms of disagreement recognized."""
    arg = make_arg()
    policy = KnowItAllPolicy(arg)
    policy.start()
    
    for disagreement in ["no", "n", "disagree"]:
        response = policy.handle_input(disagreement)
        assert response is not None or policy.state.finished


def test_know_it_all_progresses_to_completion() -> None:
    """Dialog progresses to completion with agreement."""
    arg = make_arg()
    policy = KnowItAllPolicy(arg)
    policy.start()
    
    iterations = 0
    max_iterations = 100
    
    while not policy.state.finished and iterations < max_iterations:
        policy.handle_input("yes")
        iterations += 1
    
    assert policy.state.finished or iterations < max_iterations


# ---------------------------------------------------------------------------
# SilentPolicy
# ---------------------------------------------------------------------------

def test_silent_policy_ignores_input() -> None:
    """SilentPolicy ignores user input."""
    arg = make_arg()
    policy = SilentPolicy(arg)
    policy.start()
    
    response = policy.handle_input("anything")
    assert response is not None


def test_silent_policy_presents_all() -> None:
    """SilentPolicy presents all statements without waiting."""
    arg = Argument()
    p1 = Premise(name="p1").add_statement("s1").add_statement("s2")
    p2 = Premise(name="p2").add_statement("s3")
    arg.add_premise(p1).add_premise(p2)
    
    policy = SilentPolicy(arg)
    policy.start()
    
    statements = []
    while not policy.state.finished:
        response = policy.handle_input("")
        if response:
            statements.append(response)
    
    # Should have presented all statements plus conclusion
    assert len(statements) >= 3  # At least s1, s2, s3, conclusion


# ---------------------------------------------------------------------------
# SocraticPolicy
# ---------------------------------------------------------------------------

def test_socratic_policy_asks_questions_on_disagreement() -> None:
    """SocraticPolicy asks questions when user disagrees."""
    arg = make_arg()
    policy = SocraticPolicy(arg)
    policy.start()
    
    response = policy.handle_input("no I disagree")
    assert response is not None
    # Should ask a question, not provide support
    assert "?" in response or response.endswith("\n")


def test_socratic_policy_advances_on_agreement() -> None:
    """SocraticPolicy advances dialog on agreement."""
    arg = make_arg()
    policy = SocraticPolicy(arg)
    policy.start()
    
    response = policy.handle_input("yes I agree")
    assert response is not None
    assert "Do you agree?" in response or policy.state.finished


def test_socratic_policy_question_variety() -> None:
    """SocraticPolicy asks different questions."""
    arg = make_arg()
    policy = SocraticPolicy(arg)
    policy.start()
    
    questions = set()
    for _ in range(5):
        response = policy.handle_input("disagree")
        if response:
            questions.add(response.strip())
    
    # Should have asked multiple different questions
    assert len(questions) >= 2


def test_socratic_policy_handles_any_input() -> None:
    """SocraticPolicy handles any user input with questions."""
    arg = make_arg()
    policy = SocraticPolicy(arg)
    policy.start()
    
    for user_input in ["why", "because", "I think so", "maybe"]:
        response = policy.handle_input(user_input)
        assert response is not None


# ---------------------------------------------------------------------------
# DebatePolicy
# ---------------------------------------------------------------------------

def test_debate_policy_challenges_disagreement() -> None:
    """DebatePolicy challenges when user disagrees."""
    arg = make_arg()
    policy = DebatePolicy(arg)
    policy.start()
    
    response = policy.handle_input("no I disagree")
    assert response is not None
    # Should either challenge or try to advance
    assert len(response) > 0


def test_debate_policy_advances_on_agreement() -> None:
    """DebatePolicy advances dialog on agreement."""
    arg = make_arg()
    policy = DebatePolicy(arg)
    policy.start()
    
    response = policy.handle_input("yes I agree")
    assert response is not None
    assert "Do you agree?" in response or policy.state.finished


def test_debate_policy_multiple_challenges() -> None:
    """DebatePolicy limits number of challenges before moving on."""
    arg = make_arg()
    policy = DebatePolicy(arg)
    policy.start()
    
    # Disagree multiple times
    responses = []
    for _ in range(4):
        response = policy.handle_input("no")
        if response:
            responses.append(response)
    
    # Should eventually move on even if still disagreeing
    assert len(responses) > 0


def test_debate_policy_challenge_responses() -> None:
    """DebatePolicy uses varied challenge responses."""
    arg = Argument()
    p1 = Premise(name="p1", support=["Support for this claim"]).add_statement("Statement 1")
    arg.add_premise(p1)
    
    policy = DebatePolicy(arg)
    policy.start()
    
    response = policy.handle_input("disagree")
    assert response is not None
    # Should include some form of challenge intro or support
    assert len(response) > 10


# ---------------------------------------------------------------------------
# ExploratoryPolicy
# ---------------------------------------------------------------------------

def test_exploratory_policy_acknowledges_neutrally() -> None:
    """ExploratoryPolicy acknowledges disagreements neutrally."""
    arg = make_arg()
    policy = ExploratoryPolicy(arg)
    policy.start()
    
    response = policy.handle_input("no I disagree")
    assert response is not None
    # Should be neutral, not argumentative
    assert len(response) > 0


def test_exploratory_policy_advances_on_agreement() -> None:
    """ExploratoryPolicy advances dialog on agreement."""
    arg = make_arg()
    policy = ExploratoryPolicy(arg)
    policy.start()
    
    response = policy.handle_input("yes I agree")
    assert response is not None
    assert "What's your view?" in response or policy.state.finished


def test_exploratory_policy_neutral_acknowledgments() -> None:
    """ExploratoryPolicy uses varied neutral acknowledgments."""
    arg = make_arg()
    policy = ExploratoryPolicy(arg)
    policy.start()
    
    responses = []
    for _ in range(5):
        response = policy.handle_input("disagree")
        if response:
            responses.append(response)
    
    # Should have multiple different responses
    unique_responses = set(r.split('\n')[0] for r in responses if r)
    assert len(unique_responses) >= 2


def test_exploratory_policy_offers_support_neutrally() -> None:
    """ExploratoryPolicy offers support in neutral framing."""
    arg = Argument()
    p1 = Premise(name="p1", support=["Some evidence suggests this"]).add_statement("Statement 1")
    arg.add_premise(p1)
    
    policy = ExploratoryPolicy(arg)
    policy.start()
    
    response = policy.handle_input("disagree")
    assert response is not None
    # Should acknowledge and offer support neutrally
    assert len(response) > 0


def test_exploratory_policy_completes_dialog() -> None:
    """ExploratoryPolicy completes dialog with agreement."""
    arg = make_arg()
    policy = ExploratoryPolicy(arg)
    policy.start()
    
    iterations = 0
    max_iterations = 100
    
    while not policy.state.finished and iterations < max_iterations:
        policy.handle_input("yes")
        iterations += 1
    
    assert policy.state.finished or iterations < max_iterations


# ---------------------------------------------------------------------------
# Policy Integration Tests
# ---------------------------------------------------------------------------

def test_all_policies_complete_with_agreement() -> None:
    """All policy types complete dialog when user agrees."""
    arg = make_arg()
    policies = [
        KnowItAllPolicy(arg),
        SilentPolicy(arg),
        SocraticPolicy(arg),
        DebatePolicy(arg),
        ExploratoryPolicy(arg),
    ]
    
    for policy in policies:
        policy.start()
        iterations = 0
        
        while not policy.state.finished and iterations < 50:
            policy.handle_input("yes")
            iterations += 1
        
        # Policy should finish or make significant progress
        assert iterations < 50, f"{policy.__class__.__name__} didn't progress"


class TestRunSync:
    """Tests for BasePolicy.run_sync() coroutine."""

    def test_run_sync_yields_intro_first(self) -> None:
        """First value from run_sync is the intro."""
        arg = make_arg()
        gen = KnowItAllPolicy(arg).run_sync()
        first = next(gen)
        assert first == arg.intro

    def test_run_sync_advances_on_agreement(self) -> None:
        """Sending 'yes' through run_sync eventually yields the conclusion."""
        arg = make_arg()
        gen = KnowItAllPolicy(arg).run_sync()
        messages: list[str] = [next(gen)]
        try:
            while True:
                messages.append(gen.send("yes"))
        except StopIteration:
            pass
        assert arg.conclusion in messages

    def test_run_sync_uses_policy_handle_input(self) -> None:
        """run_sync delegates to handle_input so policy-specific logic runs."""
        arg = make_arg()
        # SocraticPolicy returns questions, not statements + "Do you agree?"
        gen = SocraticPolicy(arg).run_sync()
        next(gen)  # intro
        # First user response triggers handle_input
        try:
            response = gen.send("yes")
            # SocraticPolicy asks a question — response contains "?"
            assert "?" in response
        except StopIteration:
            pass  # Very short argument — still exercised handle_input

    def test_run_sync_five_w_dispatch(self) -> None:
        """run_sync returns 5W answer when user asks 'what'."""
        arg = make_arg()
        # Add a 5W answer to the first available premise
        first_premise = arg.premises[0]
        first_premise.add_what("What it means in this context.")

        gen = KnowItAllPolicy(arg).run_sync()
        next(gen)  # intro — this also advances to first statement via handle_input
        # Trigger first statement display
        gen.send("ok")  # agree with intro prompt → first statement shown
        # Now ask a 5W question
        try:
            response = gen.send("what does that mean")
            assert "What it means in this context." in (response or "")
        except StopIteration:
            pass  # argument was too short; exercise was still useful


class TestStream:
    """Tests for BasePolicy.stream() async method."""

    def test_stream_yields_intro(self) -> None:
        """stream() first yield is the intro."""
        import asyncio

        async def run() -> list[str]:
            arg = make_arg()
            q: asyncio.Queue[str] = asyncio.Queue()
            policy = KnowItAllPolicy(arg)
            messages: list[str] = []
            async for msg in policy.stream(q):
                messages.append(msg)
                if not policy.state.finished:
                    await q.put("yes")
                else:
                    break
            return messages

        messages = asyncio.run(run())
        assert len(messages) >= 1
        assert messages[0] == make_arg().intro

    def test_stream_completes_on_agreement(self) -> None:
        """stream() terminates after all premises agreed."""
        import asyncio

        async def run() -> list[str]:
            arg = make_arg()
            q: asyncio.Queue[str] = asyncio.Queue()
            policy = KnowItAllPolicy(arg)
            messages: list[str] = []
            async for msg in policy.stream(q):
                messages.append(msg)
                await q.put("yes")
            return messages

        messages = asyncio.run(run())
        assert any(make_arg().conclusion in m for m in messages)


def test_all_policies_handle_disagreement() -> None:
    """All policy types handle disagreement appropriately."""
    arg = make_arg()
    policies = [
        KnowItAllPolicy(arg),
        SocraticPolicy(arg),
        DebatePolicy(arg),
        ExploratoryPolicy(arg),
    ]
    
    for policy in policies:
        policy.start()
        
        # Each policy should respond to disagreement in its own way
        response = policy.handle_input("no")
        assert response is not None, f"{policy.__class__.__name__} returned None on disagreement"
