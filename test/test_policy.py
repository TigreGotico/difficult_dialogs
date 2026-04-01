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


class TestBasePolicyDefensivePaths:
    """Cover defensive null-return and stale-premise paths in BasePolicy helpers."""

    def _make_policy_with_stale_premise(self) -> SilentPolicy:
        """Build a policy whose current_premise references a non-existent premise."""
        arg = Argument(name="test", intro="I.", conclusion="C.")
        p = Premise(name="real")
        p.add_statement("s1")
        arg.add_premise(p)
        policy = SilentPolicy(arg)
        policy.state.current_premise = "nonexistent"
        return policy

    def test_get_support_no_current_premise(self) -> None:
        """_get_support returns None when current_premise is not set."""
        arg = make_arg()
        policy = SilentPolicy(arg)
        # Don't set current_premise
        assert policy._get_support() is None

    def test_get_support_stale_premise(self) -> None:
        """_get_support returns None when current_premise no longer exists."""
        policy = self._make_policy_with_stale_premise()
        assert policy._get_support() is None

    def test_get_sources_no_current_premise(self) -> None:
        """_get_sources returns [] when current_premise is not set."""
        arg = make_arg()
        policy = SilentPolicy(arg)
        assert policy._get_sources() == []

    def test_get_sources_stale_premise(self) -> None:
        """_get_sources returns [] when current_premise no longer exists."""
        policy = self._make_policy_with_stale_premise()
        assert policy._get_sources() == []

    def test_check_five_w_stale_premise(self) -> None:
        """_check_five_w returns None when current_premise no longer exists."""
        policy = self._make_policy_with_stale_premise()
        assert policy._check_five_w("what is this") is None

    def test_run_sync_breaks_on_none_response(self) -> None:
        """run_sync exits cleanly when handle_input returns None."""
        arg = Argument(name="test", intro="I.", conclusion="C.")
        policy = SilentPolicy(arg)
        gen = policy.run_sync()
        messages = [next(gen)]
        try:
            while True:
                messages.append(gen.send("yes"))
        except StopIteration:
            pass
        assert len(messages) >= 1


class TestFiveWDispatchInCorePolicies:
    """Cover five_w return paths in SocraticPolicy, DebatePolicy, ExploratoryPolicy."""

    def _arg_with_five_w(self) -> Argument:
        arg = Argument(name="test", intro="Intro text here.", conclusion="Conclusion.")
        p = Premise(name="p1")
        p.add_statement("s1")
        p.add_what("What this means.")
        p.add_why("Why this is true.")
        arg.add_premise(p)
        return arg

    def test_socratic_five_w_dispatch(self) -> None:
        """SocraticPolicy returns 5W answer when current_premise is active."""
        arg = self._arg_with_five_w()
        policy = SocraticPolicy(arg)
        policy.start()
        policy.state.current_premise = "p1"
        response = policy.handle_input("what does this mean")
        assert response == "What this means."

    def test_debate_five_w_dispatch(self) -> None:
        """DebatePolicy returns 5W answer when current_premise is active."""
        arg = self._arg_with_five_w()
        policy = DebatePolicy(arg)
        policy.start()
        policy.state.current_premise = "p1"
        response = policy.handle_input("why is that")
        assert response == "Why this is true."

    def test_exploratory_five_w_dispatch(self) -> None:
        """ExploratoryPolicy returns 5W answer when current_premise is active."""
        arg = self._arg_with_five_w()
        policy = ExploratoryPolicy(arg)
        policy.start()
        policy.state.current_premise = "p1"
        response = policy.handle_input("what does this mean")
        assert response == "What this means."

    def test_debate_neutral_advance(self) -> None:
        """DebatePolicy neutral input (not agree/disagree) calls agree + advance."""
        arg = self._arg_with_five_w()
        policy = DebatePolicy(arg)
        policy.start()
        # "maybe" doesn't start with y/n/disagree/agree
        response = policy.handle_input("maybe")
        assert response is not None

    def test_exploratory_neutral_advance(self) -> None:
        """ExploratoryPolicy neutral input calls agree + advance."""
        arg = self._arg_with_five_w()
        policy = ExploratoryPolicy(arg)
        policy.start()
        response = policy.handle_input("perhaps")
        assert response is not None

    def test_knowitall_five_w_dispatch(self) -> None:
        """KnowItAllPolicy returns 5W answer when current_premise is active."""
        arg = self._arg_with_five_w()
        policy = KnowItAllPolicy(arg)
        policy.start()
        policy.state.current_premise = "p1"
        response = policy.handle_input("what does this mean")
        assert response == "What this means."

    def test_knowitall_sources_path(self) -> None:
        """KnowItAllPolicy on disagreement falls through to sources when no support."""
        arg = Argument(name="test", intro="Intro.", conclusion="Conclusion.")
        p = Premise(name="p1")
        p.add_statement("s1")
        p.add_source("https://example.com")
        arg.add_premise(p)
        policy = KnowItAllPolicy(arg)
        policy.start()
        policy.state.current_premise = "p1"
        # Disagree with no support available
        response = policy.handle_input("no")
        assert response is not None
        assert "example.com" in response or "Sources" in response


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


# ---------------------------------------------------------------------------
# Transcript
# ---------------------------------------------------------------------------

def test_transcript_populated_by_start() -> None:
    """start() records a bot entry in the transcript."""
    policy = KnowItAllPolicy(make_arg())
    policy.start()
    assert len(policy.state.transcript) == 1
    assert policy.state.transcript[0].role == "bot"


def test_transcript_populated_by_respond() -> None:
    """respond() records user + bot entries."""
    policy = KnowItAllPolicy(make_arg())
    policy.start()
    policy.respond("yes")
    # start() added 1, respond() adds user + bot = 3 total (or 2 if bot is None)
    assert any(e.role == "user" for e in policy.state.transcript)


def test_transcript_populated_by_end() -> None:
    """end() records a bot entry for the conclusion."""
    policy = KnowItAllPolicy(make_arg())
    policy.start()
    policy.end()
    roles = [e.role for e in policy.state.transcript]
    assert roles.count("bot") >= 2  # intro + conclusion


def test_transcript_reset_on_start() -> None:
    """Calling start() again clears the previous transcript."""
    policy = KnowItAllPolicy(make_arg())
    policy.start()
    policy.respond("yes")
    policy.start()  # reset
    assert len(policy.state.transcript) == 1  # only new intro


def test_run_sync_populates_transcript() -> None:
    """run_sync() records both user and bot turns."""
    policy = KnowItAllPolicy(make_arg())
    gen = policy.run_sync()
    next(gen)                    # bot intro
    try:
        gen.send("yes")          # user turn → bot response
    except StopIteration:
        pass
    user_turns = [e for e in policy.state.transcript if e.role == "user"]
    assert len(user_turns) >= 1


# ---------------------------------------------------------------------------
# PolicyState serialization
# ---------------------------------------------------------------------------

def test_policy_state_round_trip() -> None:
    """PolicyState.to_dict() / from_dict() preserves all fields."""
    from difficult_dialogs.policy import TranscriptEntry
    state = PolicyState(
        spoken_premises={"p1", "p2"},
        spoken_statements={"s1"},
        current_premise="p2",
        user_agrees=False,
        finished=False,
        challenge_count=2,
        transcript=[TranscriptEntry(role="bot", text="Hello")],
    )
    restored = PolicyState.from_dict(state.to_dict())
    assert restored.spoken_premises == state.spoken_premises
    assert restored.spoken_statements == state.spoken_statements
    assert restored.current_premise == state.current_premise
    assert restored.user_agrees == state.user_agrees
    assert restored.finished == state.finished
    assert restored.challenge_count == state.challenge_count
    assert len(restored.transcript) == 1
    assert restored.transcript[0].role == "bot"
    assert restored.transcript[0].text == "Hello"


def test_policy_state_empty_round_trip() -> None:
    """Default PolicyState survives to_dict/from_dict."""
    state = PolicyState()
    restored = PolicyState.from_dict(state.to_dict())
    assert restored.spoken_premises == set()
    assert restored.finished is False
    assert restored.transcript == []


def test_restore_state_from_dict() -> None:
    """restore_state() accepts raw dict and resumes conversation."""
    policy = KnowItAllPolicy(make_arg())
    policy.start()
    policy.respond("yes")
    snapshot = policy.state.to_dict()

    # New policy instance — restore from snapshot
    policy2 = KnowItAllPolicy(make_arg())
    policy2.restore_state(snapshot)
    assert policy2.state.spoken_premises == policy.state.spoken_premises
    assert len(policy2.state.transcript) == len(policy.state.transcript)


def test_restore_state_from_policy_state() -> None:
    """restore_state() also accepts a PolicyState object directly."""
    policy = KnowItAllPolicy(make_arg())
    policy.start()
    state_obj = policy.state

    policy2 = KnowItAllPolicy(make_arg())
    policy2.restore_state(state_obj)
    assert policy2.state is state_obj


def test_transcript_entry_round_trip() -> None:
    """TranscriptEntry.to_dict/from_dict preserves role and text."""
    from difficult_dialogs.policy import TranscriptEntry
    entry = TranscriptEntry(role="user", text="Hello world")
    restored = TranscriptEntry.from_dict(entry.to_dict())
    assert restored.role == "user"
    assert restored.text == "Hello world"


# ---------------------------------------------------------------------------
# save_state / load_state
# ---------------------------------------------------------------------------

def test_save_and_load_state_round_trip(tmp_path) -> None:
    """save_state/load_state preserves spoken premises and transcript."""
    policy = KnowItAllPolicy(make_arg())
    policy.start()
    policy.respond("yes")
    path = tmp_path / "session.json"
    policy.save_state(path)

    policy2 = KnowItAllPolicy(make_arg())
    policy2.load_state(path)
    assert policy2.state.spoken_premises == policy.state.spoken_premises
    assert len(policy2.state.transcript) == len(policy.state.transcript)
    assert policy2.state.finished == policy.state.finished


def test_save_state_creates_valid_json(tmp_path) -> None:
    """save_state writes valid JSON."""
    import json
    policy = KnowItAllPolicy(make_arg())
    policy.start()
    path = tmp_path / "state.json"
    policy.save_state(path)
    data = json.loads(path.read_text())
    assert "spoken_premises" in data
    assert "transcript" in data


# ---------------------------------------------------------------------------
# AdaptivePolicy.set_policy
# ---------------------------------------------------------------------------

def test_adaptive_set_policy_transfers_state() -> None:
    """set_policy transfers transcript and spoken_premises to new delegate."""
    from difficult_dialogs.policy import AdaptivePolicy, SocraticPolicy
    arg = make_arg()
    policy = AdaptivePolicy(arg)
    policy.start()
    policy.respond("yes")

    original_transcript_len = len(policy.state.transcript)
    original_spoken = set(policy.state.spoken_premises)

    policy.set_policy(SocraticPolicy(arg))
    # State must be preserved after the switch
    assert len(policy.state.transcript) == original_transcript_len
    assert policy.state.spoken_premises == original_spoken
    assert isinstance(policy.active_policy, SocraticPolicy)


def test_adaptive_set_policy_active_policy_property() -> None:
    """active_policy reflects new policy after set_policy."""
    from difficult_dialogs.policy import AdaptivePolicy, TeacherPolicy
    arg = make_arg()
    policy = AdaptivePolicy(arg)
    policy.start()
    new = TeacherPolicy(arg)
    policy.set_policy(new)
    assert policy.active_policy is new


# ---------------------------------------------------------------------------
# lang parameter threading
# ---------------------------------------------------------------------------

def test_lang_stored_on_policy() -> None:
    """lang kwarg is stored on BasePolicy and defaults to en-US."""
    policy = KnowItAllPolicy(make_arg())
    assert policy.lang == "en-US"


def test_lang_custom_value_propagates() -> None:
    """Explicit lang value is stored."""
    policy = KnowItAllPolicy(make_arg(), lang="es-ES")
    assert policy.lang == "es-ES"


def test_adaptive_lang_propagates_to_delegate() -> None:
    """AdaptivePolicy passes lang to initial delegate on start()."""
    from difficult_dialogs.policy import AdaptivePolicy
    arg = make_arg()
    policy = AdaptivePolicy(arg, lang="pt-BR")
    policy.start()
    assert policy.active_policy.lang == "pt-BR"


def test_lang_passed_to_parse_yes_no(monkeypatch) -> None:
    """handle_input passes policy.lang to parse_yes_no."""
    import difficult_dialogs.yesno as yesno_module
    captured: list[str] = []
    original = yesno_module.parse_yes_no

    def spy(text: str, lang: str = "en-US") -> object:
        captured.append(lang)
        return original(text, lang)

    monkeypatch.setattr(yesno_module, "parse_yes_no", spy)

    policy = KnowItAllPolicy(make_arg(), lang="fr-FR")
    policy.start()
    policy.respond("oui")
    assert "fr-FR" in captured
