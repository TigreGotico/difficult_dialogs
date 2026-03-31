"""Tests for additional dialog policies."""
import pytest
from difficult_dialogs.arguments import Argument
from difficult_dialogs.premises import Premise
from difficult_dialogs.policy import (
    MaieuticPolicy,
    SkepticPolicy,
    TeacherPolicy,
    DebaterPolicy,
    MinimalistPolicy,
    get_policy,
)


@pytest.fixture
def sample_argument() -> Argument:
    """Create sample argument for testing."""
    arg = Argument(
        name="Test Argument",
        intro="This is a test introduction.",
        conclusion="This is a test conclusion."
    )
    
    premise1 = Premise(name="premise_one")
    premise1.add_statement("Statement 1")
    premise1.add_statement("Statement 2")
    
    premise2 = Premise(name="premise_two")
    premise2.add_statement("Statement 3")
    
    arg.add_premise(premise1)
    arg.add_premise(premise2)
    
    return arg


class TestMaieuticPolicy:  # formerly TestSocraticPolicy (policies.py SocraticPolicy renamed to MaieuticPolicy)
    """Test Socratic questioning policy."""
    
    def test_start_returns_question(self, sample_argument: Argument) -> None:
        """Start should return open question."""
        policy = MaieuticPolicy(sample_argument)
        start = policy.start()
        
        assert "?" in start
        assert "test argument" in start.lower()
    
    def test_handle_input_returns_question(self, sample_argument: Argument) -> None:
        """Should respond with questions."""
        policy = MaieuticPolicy(sample_argument)
        policy.start()
        
        response = policy.handle_input("yes")
        
        assert response is not None
        assert "?" in response
    
    def test_different_questions_for_agreement(self, sample_argument: Argument) -> None:
        """Different inputs should get different questions."""
        policy = MaieuticPolicy(sample_argument)
        policy.start()
        
        agree_response = policy.handle_input("yes I agree")
        disagree_response = policy.handle_input("no I disagree")
        
        # Both should be questions
        assert "?" in agree_response
        assert "?" in disagree_response


class TestSkepticPolicy:
    """Test skeptical debate policy."""
    
    def test_challenges_agreement(self, sample_argument: Argument) -> None:
        """Should challenge when user agrees."""
        policy = SkepticPolicy(sample_argument)
        
        response = policy.handle_input("yes I agree")
        
        assert response is not None
        assert len(response) > 10  # Substantial challenge
    
    def test_provides_counters(self, sample_argument: Argument) -> None:
        """Should provide counterarguments."""
        policy = SkepticPolicy(sample_argument)
        
        response = policy.handle_input("no I disagree")
        
        # Should either challenge or counter
        assert response is not None


class TestTeacherPolicy:
    """Test educational teaching policy."""
    
    def test_explains_concepts(self, sample_argument: Argument) -> None:
        """Should provide explanations."""
        policy = TeacherPolicy(sample_argument)
        
        response = policy.handle_input("why?")
        
        assert response is not None
        assert len(response) > 20  # Explanations are longer
    
    def test_reinforces_agreement(self, sample_argument: Argument) -> None:
        """Should reinforce when user understands."""
        policy = TeacherPolicy(sample_argument)
        
        response = policy.handle_input("yes I understand now")
        
        assert response is not None
        # Teachers summarize
        assert any(word in response.lower() for word in 
                  ["summary", "takeaway", "means", "example", "illustrate"])
    
    def test_clarifies_misconceptions(self, sample_argument: Argument) -> None:
        """Should clarify when confused."""
        policy = TeacherPolicy(sample_argument)
        
        response = policy.handle_input("no I'm confused")
        
        assert response is not None
        assert "clarify" in response.lower() or "rephrase" in response.lower()


class TestDebaterPolicy:
    """Test aggressive debate policy."""
    
    def test_attacks_claims(self, sample_argument: Argument) -> None:
        """Should attack user's claims."""
        policy = DebaterPolicy(sample_argument)
        
        response = policy.handle_input("I think this is obviously true because reasons")
        
        assert response is not None
        assert any(attack in response for attack in 
                  ["flawed", "debunked", "ignoring", "fallacy", "scrutiny"])
    
    def test_defends_position(self, sample_argument: Argument) -> None:
        """Should defend when user agrees."""
        policy = DebaterPolicy(sample_argument)
        
        response = policy.handle_input("yes I agree with you")
        
        # Should provide substantial defense (not just brief acknowledgment)
        assert response is not None
        assert len(response) > 20  # Defenses are substantive


class TestMinimalistPolicy:
    """Test concise communication policy."""
    
    def test_brief_responses(self, sample_argument: Argument) -> None:
        """Responses should be brief."""
        policy = MinimalistPolicy(sample_argument)
        
        response = policy.handle_input("yes")
        
        assert response is not None
        assert len(response) <= 20  # Very brief
    
    def test_truncates_long_statements(self, sample_argument: Argument) -> None:
        """Long statements should be truncated."""
        policy = MinimalistPolicy(sample_argument)
        
        response = policy.handle_input("no")
        
        if response:
            assert len(response) <= 105  # 100 + "..."
    
    def test_direct_disagreement(self, sample_argument: Argument) -> None:
        """Should directly state disagreement."""
        policy = MinimalistPolicy(sample_argument)
        
        response = policy.handle_input("no")
        
        # Should be brief and direct (may be truncated statement or brief phrase)
        assert response is not None
        assert len(response) <= 105  # Brief


class TestPolicyRegistry:
    """Test policy lookup by name."""
    
    def test_get_maieutic_policy(self, sample_argument: Argument) -> None:
        """Should get MaieuticPolicy by name."""
        policy = get_policy("maieutic", sample_argument)

        assert isinstance(policy, MaieuticPolicy)
    
    def test_get_skeptic_policy(self, sample_argument: Argument) -> None:
        """Should get SkepticPolicy by name."""
        policy = get_policy("skeptic", sample_argument)
        
        assert isinstance(policy, SkepticPolicy)
    
    def test_get_teacher_policy(self, sample_argument: Argument) -> None:
        """Should get TeacherPolicy by name."""
        policy = get_policy("teacher", sample_argument)
        
        assert isinstance(policy, TeacherPolicy)
    
    def test_get_debater_policy(self, sample_argument: Argument) -> None:
        """Should get DebaterPolicy by name."""
        policy = get_policy("debater", sample_argument)
        
        assert isinstance(policy, DebaterPolicy)
    
    def test_get_minimalist_policy(self, sample_argument: Argument) -> None:
        """Should get MinimalistPolicy by name."""
        policy = get_policy("minimalist", sample_argument)
        
        assert isinstance(policy, MinimalistPolicy)
    
    def test_case_insensitive_lookup(self, sample_argument: Argument) -> None:
        """Lookup should be case-insensitive."""
        policy1 = get_policy("TEACHER", sample_argument)
        policy2 = get_policy("teacher", sample_argument)
        
        assert type(policy1) == type(policy2)
    
    def test_invalid_policy_raises_error(self, sample_argument: Argument) -> None:
        """Invalid name should raise InvalidPolicyError."""
        from difficult_dialogs.exceptions import InvalidPolicyError
        with pytest.raises(InvalidPolicyError) as exc_info:
            get_policy("nonexistent_policy", sample_argument)

        assert "Unknown policy" in str(exc_info.value)
        assert "Available:" in str(exc_info.value)


class TestMaieuticPolicyBranches:
    """Cover neutral-input and 5W dispatch branches in MaieuticPolicy."""

    def test_neutral_input_uses_intro_questions(self, sample_argument: Argument) -> None:
        """Input that is neither agree nor disagree falls to INTRO_QUESTIONS."""
        policy = MaieuticPolicy(sample_argument)
        policy.start()
        response = policy.handle_input("maybe")
        assert response is not None
        assert "?" in response

    def test_five_w_returned_directly(self, sample_argument: Argument) -> None:
        """5W question bypasses guided-discovery logic when a premise is active."""
        sample_argument.premises[0].add_what("What it really means.")
        policy = MaieuticPolicy(sample_argument)
        policy.start()
        policy.state.current_premise = sample_argument.premises[0].name
        response = policy.handle_input("what does this mean")
        assert response == "What it really means."

    def test_question_count_increments(self, sample_argument: Argument) -> None:
        """question_count tracks each guided question."""
        policy = MaieuticPolicy(sample_argument)
        policy.start()
        policy.handle_input("maybe")
        policy.handle_input("maybe")
        assert policy.question_count == 2


class TestSkepticPolicyBranches:
    """Cover counter-argument and default skepticism branches."""

    def test_disagree_triggers_counter_premise(self, sample_argument: Argument) -> None:
        """Disagreement returns a counter-premise statement."""
        policy = SkepticPolicy(sample_argument)
        response = policy.handle_input("no")
        assert response is not None
        # Should include one of the COUNTER_PHRASES prefix (each ends with ": " or " ")
        assert any(phrase.rstrip() in response for phrase in SkepticPolicy.COUNTER_PHRASES)

    def test_default_skepticism(self, sample_argument: Argument) -> None:
        """Neutral input falls to default skepticism message."""
        policy = SkepticPolicy(sample_argument)
        response = policy.handle_input("perhaps")
        assert response == "I need more convincing. What specific evidence can you provide?"

    def test_five_w_bypasses_challenge(self, sample_argument: Argument) -> None:
        """5W question is answered before challenge logic when a premise is active."""
        sample_argument.premises[0].add_why("Because the logic is sound.")
        policy = SkepticPolicy(sample_argument)
        policy.state.current_premise = sample_argument.premises[0].name
        response = policy.handle_input("why is that true")
        assert response == "Because the logic is sound."


class TestTeacherPolicyBranches:
    """Cover _teach_with_example and default paths."""

    def test_teach_with_example_default_path(self, sample_argument: Argument) -> None:
        """Neutral input triggers _teach_with_example with a statement."""
        policy = TeacherPolicy(sample_argument)
        response = policy.handle_input("okay")
        assert response is not None
        assert any(intro in response for intro in TeacherPolicy.EXAMPLE_INTROS)

    def test_teach_with_example_fallback_to_conclusion(self) -> None:
        """_teach_with_example returns conclusion when no statements remain."""
        arg = Argument(name="test", intro="I.", conclusion="The end.")
        p = Premise(name="p1")
        p.add_statement("s1")
        arg.add_premise(p)
        policy = TeacherPolicy(arg)
        # Exhaust all statements
        policy.state.spoken_statements.add("s1")
        policy.state.spoken_premises.add("p1")
        response = policy.handle_input("okay")
        assert response == "The end."

    def test_clarify_misconception_fallback(self) -> None:
        """_clarify_misconception returns rephrase message when no statements remain."""
        arg = Argument(name="test", intro="I.", conclusion="C.")
        p = Premise(name="p1")
        p.add_statement("s1")
        arg.add_premise(p)
        policy = TeacherPolicy(arg)
        policy.state.spoken_statements.add("s1")
        policy.state.spoken_premises.add("p1")
        response = policy.handle_input("no I'm confused")
        assert response == "Let me rephrase that more clearly."

    def test_get_explanation_fallback_to_conclusion(self) -> None:
        """_get_explanation returns conclusion when all statements spoken."""
        arg = Argument(name="test", intro="I.", conclusion="The final word.")
        p = Premise(name="p1")
        p.add_statement("s1")
        arg.add_premise(p)
        policy = TeacherPolicy(arg)
        policy.state.spoken_statements.add("s1")
        policy.state.spoken_premises.add("p1")
        # Question input calls _get_explanation
        response = policy.handle_input("what does that mean?")
        assert "The final word." in response

    def test_five_w_bypasses_teacher_logic(self, sample_argument: Argument) -> None:
        """5W answer bypasses Teacher question/agree/disagree branching."""
        sample_argument.premises[0].add_how("By using logic.")
        policy = TeacherPolicy(sample_argument)
        policy.state.current_premise = sample_argument.premises[0].name
        response = policy.handle_input("how does that work")
        assert response == "By using logic."


class TestDebaterPolicyBranches:
    """Cover disagree double-down and default present-argument paths."""

    def test_disagree_doubles_down(self, sample_argument: Argument) -> None:
        """Short 'no' input triggers double-down with next statement."""
        policy = DebaterPolicy(sample_argument)
        # "no" is <=10 chars, not 'yes'/'agree'/'fine', matches disagree branch
        response = policy.handle_input("no")
        assert response is not None
        assert response.startswith("Exactly!")

    def test_default_presents_next_statement(self, sample_argument: Argument) -> None:
        """Short neutral input with no agree/disagree falls to default branch."""
        policy = DebaterPolicy(sample_argument)
        # Short input (<=10 chars) that is neither agree nor disagree
        response = policy.handle_input("ok then")
        assert response is not None

    def test_attack_without_next_statement(self) -> None:
        """Attack-only path when all statements exhausted."""
        arg = Argument(name="test", intro="I.", conclusion="C.")
        p = Premise(name="p1")
        p.add_statement("s1")
        arg.add_premise(p)
        policy = DebaterPolicy(arg)
        policy.state.spoken_statements.add("s1")
        policy.state.spoken_premises.add("p1")
        # Long input triggers attack branch
        response = policy.handle_input("I think this argument is certainly true")
        assert response in DebaterPolicy.ATTACK_PHRASES

    def test_default_falls_to_conclusion_when_exhausted(self) -> None:
        """Short neutral input with no statements returns conclusion."""
        arg = Argument(name="test", intro="I.", conclusion="Final.")
        p = Premise(name="p1")
        p.add_statement("s1")
        arg.add_premise(p)
        policy = DebaterPolicy(arg)
        policy.state.spoken_statements.add("s1")
        policy.state.spoken_premises.add("p1")
        response = policy.handle_input("ok")
        assert response == "Final."

    def test_agree_returns_defense_phrase(self, sample_argument: Argument) -> None:
        """'yes' input returns a DEFENSE_PHRASES response."""
        policy = DebaterPolicy(sample_argument)
        response = policy.handle_input("yes")
        assert response in DebaterPolicy.DEFENSE_PHRASES

    def test_five_w_bypasses_debater_logic(self, sample_argument: Argument) -> None:
        """5W answer bypasses Debater attack/agree/disagree branching."""
        sample_argument.premises[0].add_what("A structured claim.")
        policy = DebaterPolicy(sample_argument)
        policy.state.current_premise = sample_argument.premises[0].name
        response = policy.handle_input("what is this")
        assert response == "A structured claim."


class TestMinimalistPolicyBranches:
    """Cover no-next-statement disagree and default present-statement paths."""

    def test_disagree_no_statements_returns_brief_disagree(self) -> None:
        """Disagreement with no remaining statements returns BRIEF_DISAGREE."""
        arg = Argument(name="test", intro="I.", conclusion="C.")
        p = Premise(name="p1")
        p.add_statement("s1")
        arg.add_premise(p)
        policy = MinimalistPolicy(arg)
        policy.state.spoken_statements.add("s1")
        policy.state.spoken_premises.add("p1")
        response = policy.handle_input("no")
        assert response in MinimalistPolicy.BRIEF_DISAGREE

    def test_default_presents_statement_truncated(self, sample_argument: Argument) -> None:
        """Neutral input presents next statement (truncated at 100 chars)."""
        policy = MinimalistPolicy(sample_argument)
        response = policy.handle_input("hmm")
        assert response is not None
        assert len(response) <= 103  # 100 chars + "..."

    def test_default_falls_to_conclusion_when_exhausted(self) -> None:
        """Default path returns conclusion when all statements spoken."""
        arg = Argument(name="test", intro="I.", conclusion="Short end.")
        p = Premise(name="p1")
        p.add_statement("s1")
        arg.add_premise(p)
        policy = MinimalistPolicy(arg)
        policy.state.spoken_statements.add("s1")
        policy.state.spoken_premises.add("p1")
        response = policy.handle_input("hmm")
        assert response == "Short end."

    def test_five_w_truncated_in_minimalist(self, sample_argument: Argument) -> None:
        """5W answer is truncated to 100 chars in MinimalistPolicy."""
        long_text = "Because " + "x" * 200
        sample_argument.premises[0].add_why(long_text)
        policy = MinimalistPolicy(sample_argument)
        policy.state.current_premise = sample_argument.premises[0].name
        response = policy.handle_input("why")
        assert response is not None
        assert response.endswith("...")
        assert len(response) == 103  # 100 chars + "..."


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
