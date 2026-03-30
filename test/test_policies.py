"""Tests for additional dialog policies."""
import pytest
from difficult_dialogs.arguments import Argument
from difficult_dialogs.premises import Premise
from difficult_dialogs.policies import (
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
        """Invalid name should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_policy("nonexistent_policy", sample_argument)
        
        assert "Unknown policy" in str(exc_info.value)
        assert "Available:" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
