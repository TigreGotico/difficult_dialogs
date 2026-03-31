"""Additional dialog policies for varied debate styles.

Extends the base policy module with specialized strategies:
- Maieutic: Guide user to discover the argument through topic-aware questions
- Skeptic: Challenge every claim rigorously
- Teacher: Explain concepts patiently with examples
- Debater: Present counterarguments aggressively
- Minimalist: Use brief, concise responses
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

from difficult_dialogs.exceptions import InvalidPolicyError
from difficult_dialogs.policy import BasePolicy

if TYPE_CHECKING:
    from difficult_dialogs.arguments import Argument


class MaieuticPolicy(BasePolicy):
    """Maieutic (guided-discovery) method — leads user to the argument via questions.

    Unlike ``SocraticPolicy`` in ``policy.py`` (which asks generic probing
    questions), this policy injects the argument's topic into question
    templates, making the questions feel contextually grounded.  The goal is
    for the user to arrive at the conclusion themselves through reflection
    rather than being told what to think.

    Best for: self-directed learning, philosophy seminars, coaching contexts.
    """

    # Question templates for different situations — {topic} is filled at runtime
    INTRO_QUESTIONS: list[str] = [
        "Have you ever considered {topic}?",
        "What are your thoughts on {topic}?",
        "Why do you think {topic} is important?",
    ]

    AGREEMENT_QUESTIONS: list[str] = [
        "What evidence supports that view?",
        "How does that connect to broader principles?",
        "What would someone who disagrees say?",
    ]

    DISAGREEMENT_QUESTIONS: list[str] = [
        "What makes you skeptical?",
        "Can you think of any counterexamples?",
        "What additional information would change your mind?",
    ]

    def __init__(self, argument: Argument) -> None:
        """Initialize MaieuticPolicy.

        Args:
            argument: The argument to guide the user toward.
        """
        super().__init__(argument)
        self.question_count: int = 0

    def handle_input(self, user_input: str) -> str | None:
        """Respond with a topic-aware question based on user input.

        Five-Ws questions are answered directly from premise data before
        falling through to guided-discovery questions.

        Args:
            user_input: User's message.

        Returns:
            A contextual question string.
        """
        user_lower = user_input.lower().strip()

        five_w = self._check_five_w(user_lower)
        if five_w:
            return five_w

        is_agreement = any(word in user_lower for word in ['yes', 'agree', 'yep', 'true'])
        is_disagreement = any(word in user_lower for word in ['no', 'disagree', 'false', 'wrong'])

        if is_disagreement:
            templates = self.DISAGREEMENT_QUESTIONS
        elif is_agreement:
            templates = self.AGREEMENT_QUESTIONS
        else:
            templates = self.INTRO_QUESTIONS

        template = random.choice(templates)
        topic = self.argument.name.replace("_", " ")
        self.question_count += 1
        return template.format(topic=topic)

    def start(self) -> str:
        """Start with an open topic question instead of the argument intro.

        Returns:
            Opening question string.
        """
        topic = self.argument.name.replace("_", " ")
        return f"Let's explore: {topic}. What's your initial perspective?"


class SkepticPolicy(BasePolicy):
    """Skeptical debater - challenges every claim.
    
    Assumes disagreement by default and requires strong evidence.
    Useful for stress-testing arguments.
    """
    
    CHALLENGE_PHRASES = [
        "That's a bold claim. What's your strongest evidence?",
        "I'm not convinced. Many experts disagree.",
        "Correlation doesn't imply causation. How do you know?",
        "That seems like an oversimplification.",
        "What about alternative explanations?",
        "How do you rule out confounding factors?",
        "Isn't that just anecdotal evidence?",
        "What's the sample size on that?",
    ]
    
    COUNTER_PHRASES = [
        "But consider this: ",
        "However, there's another perspective: ",
        "On the other hand: ",
        "A contrary view suggests: ",
    ]
    
    def handle_input(self, user_input: str) -> str | None:
        """Challenge the user's position.

        Five-Ws questions are answered directly before entering challenge logic.

        Args:
            user_input: User's message.

        Returns:
            Challenge text or a factual 5W answer.
        """
        user_lower = user_input.lower().strip()

        five_w = self._check_five_w(user_lower)
        if five_w:
            return five_w

        # If user agrees, challenge them harder
        if any(word in user_lower for word in ['yes', 'agree', 'yep']):
            return random.choice(self.CHALLENGE_PHRASES)
        
        # If user disagrees, provide counterargument
        if any(word in user_lower for word in ['no', 'disagree']):
            # Get next premise as counter
            next_stmt = self._get_next_statement()
            if next_stmt:
                _, statement = next_stmt
                prefix = random.choice(self.COUNTER_PHRASES)
                return f"{prefix}{statement}"
        
        # Default: express skepticism
        return "I need more convincing. What specific evidence can you provide?"


class TeacherPolicy(BasePolicy):
    """Patient educator - explains with examples.
    
    Focuses on clarity and understanding rather than winning.
    Provides analogies and real-world examples.
    """
    
    TRANSITION_PHRASES = [
        "Great question! Let me explain further.",
        "I'm glad you asked. Here's why:",
        "That's an important point. Consider this:",
        "Let's break this down step by step.",
    ]
    
    EXAMPLE_INTROS = [
        "For example, ",
        "To illustrate, ",
        "Think of it like this: ",
        "A real-world case is ",
    ]
    
    SUMMARY_PHRASES = [
        "So in summary, ",
        "The key takeaway is: ",
        "What this means is: ",
    ]
    
    def __init__(self, argument: Argument) -> None:
        """Initialize Teacher policy."""
        super().__init__(argument)
        self.explaining = False
    
    def handle_input(self, user_input: str) -> str | None:
        """Provide educational response.

        Five-Ws questions are answered directly from premise data.

        Args:
            user_input: User's message.

        Returns:
            Educational response or a factual 5W answer.
        """
        user_lower = user_input.lower().strip()

        five_w = self._check_five_w(user_lower)
        if five_w:
            return five_w

        # User asked a question
        if '?' in user_input:
            return random.choice(self.TRANSITION_PHRASES) + " " + self._get_explanation()
        
        # User agrees - reinforce learning
        if any(word in user_lower for word in ['yes', 'agree', 'understand']):
            return self._reinforce_concept()
        
        # User disagrees - clarify misconception
        if any(word in user_lower for word in ['no', 'disagree', 'confused']):
            return self._clarify_misconception()
        
        # Default: provide explanation with example
        return self._teach_with_example()
    
    def _get_explanation(self) -> str:
        """Get explanatory content."""
        next_stmt = self._get_next_statement()
        if next_stmt:
            return next_stmt[1]
        return self.argument.conclusion
    
    def _reinforce_concept(self) -> str:
        """Reinforce understood concept."""
        explanation = self._get_explanation()
        summary = random.choice(self.SUMMARY_PHRASES)
        return f"{summary}{explanation}"
    
    def _clarify_misconception(self) -> str:
        """Clarify misunderstood point."""
        next_stmt = self._get_next_statement()
        if next_stmt:
            _, statement = next_stmt
            return f"Let me clarify: {statement}"
        return "Let me rephrase that more clearly."
    
    def _teach_with_example(self) -> str:
        """Teach using example."""
        next_stmt = self._get_next_statement()
        if next_stmt:
            _, statement = next_stmt
            example_intro = random.choice(self.EXAMPLE_INTROS)
            return f"{example_intro}{statement}"
        return self.argument.conclusion


class DebaterPolicy(BasePolicy):
    """Aggressive debater - presents strong counterarguments.
    
    Takes opposing stance and defends it vigorously.
    Good for practicing argumentation skills.
    """
    
    ATTACK_PHRASES = [
        "Your position is fundamentally flawed.",
        "That argument has been thoroughly debunked.",
        "You're ignoring critical evidence.",
        "That's a logical fallacy.",
        "Your reasoning doesn't hold up to scrutiny.",
    ]
    
    DEFENSE_PHRASES = [
        "My position is supported by substantial evidence.",
        "The data clearly shows otherwise.",
        "Multiple studies confirm my view.",
        "Expert consensus contradicts your claim.",
    ]
    
    def __init__(self, argument: Argument) -> None:
        """Initialize Debater policy.

        Args:
            argument: The argument to debate.
        """
        super().__init__(argument)
        self.points_made: int = 0
    
    def handle_input(self, user_input: str) -> str | None:
        """Present counterarguments.

        Five-Ws questions are answered directly before entering debate logic.

        Args:
            user_input: User's message.

        Returns:
            Counterargument or a factual 5W answer.
        """
        user_lower = user_input.lower().strip()

        five_w = self._check_five_w(user_lower)
        if five_w:
            return five_w

        # User made a claim - attack it
        if len(user_lower) > 10:  # Substantial input
            attack = random.choice(self.ATTACK_PHRASES)
            
            # Follow with counter-premise
            next_stmt = self._get_next_statement()
            if next_stmt:
                _, counter = next_stmt
                return f"{attack} {counter}"
            
            return attack
        
        # User agreed (reluctantly)
        if any(word in user_lower for word in ['yes', 'agree', 'fine']):
            return random.choice(self.DEFENSE_PHRASES)
        
        # User disagreed
        if any(word in user_lower for word in ['no', 'disagree']):
            # Double down
            next_stmt = self._get_next_statement()
            if next_stmt:
                _, statement = next_stmt
                return f"Exactly! {statement}"
        
        # Default: present argument
        next_stmt = self._get_next_statement()
        if next_stmt:
            return next_stmt[1]
        
        return self.argument.conclusion


class MinimalistPolicy(BasePolicy):
    """Concise communicator - brief and direct.
    
    Uses minimal words. Gets straight to the point.
    Good for quick debates or mobile interfaces.
    """
    
    BRIEF_AGREE = [
        "Agreed.",
        "True.",
        "Correct.",
        "Yes.",
        "Right.",
    ]
    
    BRIEF_DISAGREE = [
        "Disagree.",
        "Wrong.",
        "Incorrect.",
        "No.",
        "False.",
    ]
    
    BRIEF_STATEMENTS = [
        "Here's why:",
        "Evidence:",
        "Fact:",
        "Reality:",
        "Truth:",
    ]
    
    def handle_input(self, user_input: str) -> str | None:
        """Respond briefly.

        Five-Ws questions are answered directly (truncated to 100 chars for
        brevity) before entering agree/disagree logic.

        Args:
            user_input: User's message.

        Returns:
            Brief response or a truncated 5W answer.
        """
        user_lower = user_input.lower().strip()

        five_w = self._check_five_w(user_lower)
        if five_w:
            return five_w[:100] + ("..." if len(five_w) > 100 else "")

        # User agrees
        if any(word in user_lower for word in ['yes', 'agree', 'yep']):
            return random.choice(self.BRIEF_AGREE)
        
        # User disagrees
        if any(word in user_lower for word in ['no', 'disagree', 'nah']):
            next_stmt = self._get_next_statement()
            if next_stmt:
                _, stmt = next_stmt
                # Truncate to first 50 chars
                brief = stmt[:50] + ("..." if len(stmt) > 50 else "")
                return f"{random.choice(self.BRIEF_STATEMENTS)} {brief}"
            return random.choice(self.BRIEF_DISAGREE)
        
        # Just present next statement briefly
        next_stmt = self._get_next_statement()
        if next_stmt:
            _, stmt = next_stmt
            return stmt[:100] + ("..." if len(stmt) > 100 else "")
        
        return self.argument.conclusion[:100]


from difficult_dialogs.policy import (  # noqa: E402
    KnowItAllPolicy,
    SilentPolicy,
    SocraticPolicy,
    DebatePolicy,
    ExploratoryPolicy,
)

# Registry mapping lowercase names to policy classes.
# Includes all policies from both policy.py and policies.py.
POLICY_REGISTRY: dict[str, type[BasePolicy]] = {
    "knowitall": KnowItAllPolicy,
    "silent": SilentPolicy,
    "socratic": SocraticPolicy,
    "debate": DebatePolicy,
    "exploratory": ExploratoryPolicy,
    "maieutic": MaieuticPolicy,
    "skeptic": SkepticPolicy,
    "teacher": TeacherPolicy,
    "debater": DebaterPolicy,
    "minimalist": MinimalistPolicy,
}


def get_policy(name: str, argument: Argument) -> BasePolicy:
    """Get policy instance by name.
    
    Args:
        name: Policy name (case-insensitive).
        argument: Argument to apply policy to.
        
    Returns:
        Policy instance.
        
    Raises:
        ValueError: If policy name not recognized.
    """
    name_lower = name.lower().strip()
    
    if name_lower not in POLICY_REGISTRY:
        available = ", ".join(POLICY_REGISTRY.keys())
        raise InvalidPolicyError(f"Unknown policy: {name_lower!r}. Available: {available}")
    
    policy_class = POLICY_REGISTRY[name_lower]
    return policy_class(argument)
