"""Policy module - controls dialog flow and user interaction.

Policies decide how conversations progress through an argument's premises.

All 10 concrete policy classes are defined here along with POLICY_REGISTRY
and get_policy() for runtime lookup by name.
"""
from __future__ import annotations

import asyncio
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, AsyncGenerator, Generator

from difficult_dialogs.exceptions import InvalidPolicyError

if TYPE_CHECKING:
    from difficult_dialogs.arguments import Argument


@dataclass
class TranscriptEntry:
    """A single turn in the conversation transcript."""
    role: str   # "bot" or "user"
    text: str

    def to_dict(self) -> dict[str, str]:
        """Serialise to a plain dict."""
        return {"role": self.role, "text": self.text}

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> TranscriptEntry:
        """Restore from a plain dict."""
        return cls(role=data["role"], text=data["text"])


@dataclass
class PolicyState:
    """Tracks the current state of a dialog session."""
    spoken_premises: set[str] = field(default_factory=set)
    spoken_statements: set[str] = field(default_factory=set)
    current_premise: str | None = None
    user_agrees: bool = True
    finished: bool = False
    challenge_count: int = 0
    transcript: list[TranscriptEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialise state to a JSON-safe dict for persistence.

        Returns:
            Dictionary suitable for ``json.dumps`` / storage in Redis, a DB,
            or any other session store.
        """
        return {
            "spoken_premises": sorted(self.spoken_premises),
            "spoken_statements": sorted(self.spoken_statements),
            "current_premise": self.current_premise,
            "user_agrees": self.user_agrees,
            "finished": self.finished,
            "challenge_count": self.challenge_count,
            "transcript": [e.to_dict() for e in self.transcript],
        }

    @classmethod
    def from_dict(cls, data: dict) -> PolicyState:
        """Restore state from a serialised dict.

        Args:
            data: Dict previously produced by ``to_dict()``.

        Returns:
            Populated ``PolicyState`` instance.
        """
        return cls(
            spoken_premises=set(data.get("spoken_premises", [])),
            spoken_statements=set(data.get("spoken_statements", [])),
            current_premise=data.get("current_premise"),
            user_agrees=data.get("user_agrees", True),
            finished=data.get("finished", False),
            challenge_count=data.get("challenge_count", 0),
            transcript=[
                TranscriptEntry.from_dict(e)
                for e in data.get("transcript", [])
            ],
        )


class BasePolicy(ABC):
    """Abstract base class for dialog policies.
    
    Policies control how an argument is presented to the user.
    Subclasses must implement handle_input() to process user responses.
    
    Attributes:
        argument: The argument being presented.
        state: Current dialog state.
    """
    
    def __init__(self, argument: Argument) -> None:
        """Initialize policy with an argument.
        
        Args:
            argument: Argument instance to present.
        """
        self.argument = argument
        self.state = PolicyState()
        self._output_queue: list[str] = []
    
    @abstractmethod
    def handle_input(self, user_input: str) -> str | None:
        """Process user input and return bot response.
        
        Args:
            user_input: Text input from user.
            
        Returns:
            Response text, or None to wait for more input.
        """
        raise NotImplementedError
    
    def start(self) -> str:
        """Start the dialog and return intro statement.

        Returns:
            Intro statement text.
        """
        self.state = PolicyState()
        intro = str(self.argument.intro)
        self.state.transcript.append(TranscriptEntry(role="bot", text=intro))
        return intro

    def end(self) -> str:
        """End the dialog and return conclusion.

        Returns:
            Conclusion statement text.
        """
        self.state.finished = True
        conclusion = str(self.argument.conclusion)
        self.state.transcript.append(TranscriptEntry(role="bot", text=conclusion))
        return conclusion

    def respond(self, user_input: str) -> str | None:
        """Record user input in transcript, then delegate to handle_input.

        Prefer calling this over ``handle_input`` directly so that the full
        conversation is captured in ``state.transcript``.

        Args:
            user_input: Text input from user.

        Returns:
            Response text, or None.
        """
        self.state.transcript.append(TranscriptEntry(role="user", text=user_input))
        response = self.handle_input(user_input)
        if response:
            self.state.transcript.append(TranscriptEntry(role="bot", text=response))
        return response
    
    def _get_next_statement(self) -> tuple[str, str] | None:
        """Get the next statement to present.
        
        Returns:
            Tuple of (premise_name, statement_text), or None if complete.
        """
        
        # Try current premise first
        if self.state.current_premise:
            premise = self.argument.get_premise(self.state.current_premise)
            if premise:
                stmt = premise.get_next_statement(self.state.spoken_statements)
                if stmt:
                    self.state.spoken_statements.add(stmt.text)
                    return (self.state.current_premise, stmt.text)
        
        # Move to next premise
        premise = self.argument.get_next_premise(self.state.spoken_premises)
        if premise:
            self.state.current_premise = premise.name
            self.state.spoken_premises.add(premise.name)
            stmt = premise.get_next_statement(self.state.spoken_statements)
            if stmt:
                self.state.spoken_statements.add(stmt.text)
                return (premise.name, stmt.text)
        
        # No more statements
        return None
    
    def _get_support(self) -> str | None:
        """Get support statement for current premise.
        
        Returns:
            Support text, or None if exhausted.
        """
        if not self.state.current_premise:
            return None
        
        premise = self.argument.get_premise(self.state.current_premise)
        if not premise:
            return None
        
        support = premise.get_support(self.state.spoken_statements)
        if support:
            self.state.spoken_statements.add(support)
        return str(support) if support else None
    
    def _get_sources(self) -> list[str]:
        """Get sources for current premise.

        Returns:
            List of source URLs/citations.
        """
        if not self.state.current_premise:
            return []

        premise = self.argument.get_premise(self.state.current_premise)
        if not premise:
            return []

        return list(premise.sources)

    def _check_five_w(self, user_input: str) -> str | None:
        """Check whether user input contains a Five-Ws question and return an answer.

        Checks for the keywords ``what``, ``why``, ``how``, ``when``, and
        ``where`` in the (already lowercased) user input and returns a random
        answer from the corresponding list on the current premise.

        Args:
            user_input: Lowercased, stripped user input.

        Returns:
            Answer text if a matching 5W field is populated, else ``None``.
        """
        if not self.state.current_premise:
            return None

        premise = self.argument.get_premise(self.state.current_premise)
        if not premise:
            return None

        for keyword, items in (
            ("what", premise.what),
            ("why", premise.why),
            ("how", premise.how),
            ("when", premise.when),
            ("where", premise.where),
            ("who", premise.who),
        ):
            if keyword in user_input and items:
                return random.choice(items)

        return None

    def restore_state(self, state: PolicyState | dict) -> None:
        """Restore a previously serialised session state.

        Accepts either a :class:`PolicyState` instance or a raw dict
        (as returned by ``PolicyState.to_dict()``) so callers can load
        directly from JSON / Redis without a separate deserialisation step.

        Args:
            state: ``PolicyState`` or ``dict`` to restore from.
        """
        if isinstance(state, dict):
            self.state = PolicyState.from_dict(state)
        else:
            self.state = state

    def agree(self) -> None:
        """Mark current premise as agreed."""
        self.state.user_agrees = True

    def disagree(self) -> None:
        """Mark current premise as disagreed."""
        self.state.user_agrees = False
    
    def run_sync(self) -> Generator[str, str, None]:
        """Run dialog synchronously via Python's coroutine-send protocol.

        Yields the intro first, then on each ``send()`` call passes the
        received user text through ``handle_input()`` so that the active
        policy's full logic runs — including Five-Ws dispatch, Socratic
        questioning, debate challenges, etc.

        Usage::

            gen = policy.run_sync()
            text = next(gen)          # receive intro
            while True:
                try:
                    text = gen.send(input("> "))
                    print(text)
                except StopIteration:
                    break

        Yields:
            Bot responses (intro, statements with prompts, conclusion).

        Receives:
            User input strings via ``send()``.
        """
        response: str | None = self.start()

        while True:
            if not response:
                break
            user_input = yield response
            self.state.transcript.append(TranscriptEntry(role="user", text=user_input or ""))
            response = self.handle_input(user_input or "")
            if response:
                self.state.transcript.append(TranscriptEntry(role="bot", text=response))
            if self.state.finished or response is None:
                yield self.end()
                break

    async def stream(self, user_input_stream: asyncio.Queue[str]) -> AsyncGenerator[str, None]:
        """Run dialog asynchronously with a user-input queue.

        Delegates each user message to ``handle_input()`` so that the active
        policy's full logic applies — identical to ``run_sync`` but async.

        Args:
            user_input_stream: ``asyncio.Queue`` that receives user messages.

        Yields:
            Bot responses.

        Example::

            q: asyncio.Queue[str] = asyncio.Queue()
            async for msg in policy.stream(q):
                print(msg)
                q.put_nowait(await get_user_input())
        """
        yield self.start()

        while not self.state.finished:
            user_input = await user_input_stream.get()
            response = self.respond(user_input)
            if response:
                yield response
            if self.state.finished:
                yield self.end()
                break


class KnowItAllPolicy(BasePolicy):
    """Policy that provides support arguments when user disagrees.
    
    This policy attempts to persuade the user by offering supporting
    evidence and sources when they disagree with a statement.
    """
    
    def __init__(self, argument: Argument) -> None:
        """Initialize policy.
        
        Args:
            argument: Argument to present.
        """
        super().__init__(argument)
        self._pending_response: str | None = None
    
    def handle_input(self, user_input: str) -> str | None:
        """Process user input and generate response.
        
        Handles:
        - Agreement (y/yes)
        - Disagreement (n/no)
        - Questions (what, why, how, when, where)
        
        Args:
            user_input: User's message.
            
        Returns:
            Bot response, or None if waiting for more input.
        """
        user_input = user_input.strip().lower()

        # Dispatch Five-Ws questions before agree/disagree logic
        five_w = self._check_five_w(user_input)
        if five_w:
            return five_w

        # Handle agreement/disagreement
        if user_input.startswith(('y', 'yes', 'ok', 'sure', 'agree')):
            self.agree()
            return self._advance()
        
        elif user_input.startswith(('n', 'no', 'disagree')):
            self.disagree()
            return self._handle_disagreement()
        
        # Default: advance to next statement
        self.agree()
        return self._advance()
    
    def _advance(self) -> str | None:
        """Advance to next statement.
        
        Returns:
            Next statement with prompt, or conclusion if done.
        """
        result = self._get_next_statement()
        
        if result is None:
            self.state.finished = True
            return str(self.argument.conclusion)
        
        premise_name, statement = result
        return f"{statement}\nDo you agree? (y/n) "
    
    def _handle_disagreement(self) -> str:
        """Handle user disagreement.
        
        Returns:
            Support statement or sources.
        """
        support = self._get_support()
        
        if support:
            return f"{support}\nDo you agree now? (y/n) "
        
        sources = self._get_sources()
        if sources:
            self.state.finished = True
            return "Sources:\n" + "\n".join(sources) + "\n\n" + str(self.argument.conclusion)
        
        # No support available, acknowledge and move on
        self.agree()
        return self._advance() or "Let's agree to disagree."


class SilentPolicy(BasePolicy):
    """Policy that presents all statements without waiting for feedback.
    
    Useful for one-way presentations or logging.
    """
    
    def handle_input(self, user_input: str) -> str | None:
        """Ignore input and advance.
        
        Args:
            user_input: Ignored.
            
        Returns:
            Next statement.
        """
        return self._advance()
    
    def _advance(self) -> str | None:
        """Advance to next statement.
        
        Returns:
            Next statement, or conclusion if done.
        """
        result = self._get_next_statement()
        
        if result is None:
            self.state.finished = True
            return str(self.argument.conclusion)
        
        premise_name, statement = result
        return statement


class SocraticPolicy(BasePolicy):
    """Policy that asks probing questions instead of providing answers.
    
    This policy uses the Socratic method - when users disagree, it asks
    follow-up questions to help them examine their reasoning rather than
    providing counter-arguments or sources.
    
    Best for: Educational contexts, critical thinking practice, philosophy.
    """
    
    SOCRATIC_QUESTIONS: list[str] = [
        "What makes you say that?",
        "Can you explain your reasoning?",
        "What evidence would change your mind?",
        "How does this relate to what we discussed earlier?",
        "What assumptions are you making?",
        "Could there be another explanation?",
        "What are the implications of your position?",
        "How would you respond to someone who disagrees?",
    ]
    
    def __init__(self, argument: Argument) -> None:
        """Initialize policy.
        
        Args:
            argument: Argument to present.
        """
        super().__init__(argument)
        self._last_question: str | None = None
    
    def handle_input(self, user_input: str) -> str | None:
        """Process user input with Socratic questioning.

        Five-Ws questions (what/why/how/when/where) are answered directly
        from the premise data before falling through to Socratic probing.

        Args:
            user_input: User's message.

        Returns:
            Socratic question or next statement.
        """
        user_input = user_input.strip().lower()

        five_w = self._check_five_w(user_input)
        if five_w:
            return five_w

        # Handle agreement/disagreement
        if user_input.startswith(('y', 'yes', 'ok', 'sure', 'agree')):
            self.agree()
            return self._advance()

        elif user_input.startswith(('n', 'no', 'disagree')):
            self.disagree()
            return self._ask_question()

        # Any other input - ask clarifying question
        return self._ask_question()
    
    def _ask_question(self) -> str:
        """Ask a Socratic question.
        
        Returns:
            Question text.
        """
        # Pick a question different from last time
        available = [q for q in self.SOCRATIC_QUESTIONS if q != self._last_question]
        question = random.choice(available)
        self._last_question = question
        
        return f"{question}\n"
    
    def _advance(self) -> str | None:
        """Advance to next statement.
        
        Returns:
            Next statement with prompt, or conclusion if done.
        """
        result = self._get_next_statement()
        
        if result is None:
            self.state.finished = True
            return str(self.argument.conclusion)
        
        premise_name, statement = result
        return f"{statement}\nDo you agree? (y/n) "


class DebatePolicy(BasePolicy):
    """Policy that actively argues against the user's position.
    
    This policy takes an adversarial stance - it challenges disagreements
    with counter-arguments and tries to defend the original position.
    More confrontational than KnowItAllPolicy.
    
    Best for: Debate practice, steel-manning exercises, testing convictions.
    """
    
    CHALLENGE_RESPONSES: list[str] = [
        "But consider this: ",
        "However, one could argue: ",
        "On the other hand: ",
        "A strong counter-argument is: ",
        "Let me challenge that: ",
        "I understand your point, but: ",
        "Respectfully, I disagree because: ",
        "That's a common objection, yet: ",
    ]
    
    def __init__(self, argument: Argument) -> None:
        """Initialize policy.
        
        Args:
            argument: Argument to present.
        """
        super().__init__(argument)

    def handle_input(self, user_input: str) -> str | None:
        """Process user input with debate-style responses.

        Five-Ws questions are answered directly before entering challenge logic.

        Args:
            user_input: User's message.

        Returns:
            Challenge, support, or next statement.
        """
        user_input = user_input.strip().lower()

        five_w = self._check_five_w(user_input)
        if five_w:
            return five_w

        # Handle agreement
        if user_input.startswith(('y', 'yes', 'ok', 'sure', 'agree')):
            self.agree()
            self.state.challenge_count = 0
            return self._advance()

        # Handle disagreement with active challenging
        elif user_input.startswith(('n', 'no', 'disagree')):
            self.disagree()
            return self._challenge()

        # Default: treat as neutral, advance
        self.agree()
        return self._advance()
    
    def _challenge(self) -> str:
        """Present a challenge to user's position.
        
        First tries support statements, then general challenges.
        
        Returns:
            Challenge text.
        """
        # Try to get specific support first
        support = self._get_support()
        
        if support:
            intro = random.choice(self.CHALLENGE_RESPONSES)
            self.state.challenge_count += 1
            return f"{intro}{support}\n\nDo you still disagree? (y/n) "

        # No specific support - use generic challenge
        self.state.challenge_count += 1
        if self.state.challenge_count >= 2:
            # After 2 challenges, move on
            self.agree()
            return self._advance() or "I see you're not convinced. Let's continue."
        
        return "I don't have more arguments on this point, but I maintain my position.\nShall we move on? (y/n) "
    
    def _advance(self) -> str | None:
        """Advance to next statement.
        
        Returns:
            Next statement with prompt, or conclusion if done.
        """
        result = self._get_next_statement()
        
        if result is None:
            self.state.finished = True
            return str(self.argument.conclusion)
        
        premise_name, statement = result
        return f"{statement}\nDo you agree? (y/n) "


class ExploratoryPolicy(BasePolicy):
    """Policy that presents multiple viewpoints neutrally.
    
    This policy acknowledges complexity - when users disagree, it suggests
    that reasonable people can disagree and presents the issue as nuanced.
    
    Best for: Controversial topics, balanced education, avoiding bias.
    """
    
    NEUTRAL_ACKNOWLEDGMENTS: list[str] = [
        "That's a reasonable perspective.",
        "Many people share that view.",
        "This is indeed a complex issue.",
        "There are valid points on both sides.",
        "This topic has nuance worth considering.",
        "Reasonable people can disagree here.",
        "The evidence isn't entirely clear-cut.",
        "This deserves careful consideration.",
    ]
    
    def __init__(self, argument: Argument) -> None:
        """Initialize policy.
        
        Args:
            argument: Argument to present.
        """
        super().__init__(argument)
    
    def handle_input(self, user_input: str) -> str | None:
        """Process user input with neutral exploration.

        Five-Ws questions receive a direct factual answer before the
        neutral-acknowledgment path is taken.

        Args:
            user_input: User's message.

        Returns:
            Neutral acknowledgment or next statement.
        """
        user_input = user_input.strip().lower()

        five_w = self._check_five_w(user_input)
        if five_w:
            return five_w

        # Handle agreement
        if user_input.startswith(('y', 'yes', 'ok', 'sure', 'agree')):
            self.agree()
            return self._advance()
        
        # Handle disagreement with neutral acknowledgment
        elif user_input.startswith(('n', 'no', 'disagree')):
            self.disagree()
            acknowledgment = random.choice(self.NEUTRAL_ACKNOWLEDGMENTS)
            
            # Still offer support/sources but framed neutrally
            support = self._get_support()
            if support:
                return f"{acknowledgment}\n\nSome perspectives on this topic include: {support}\n\nWhat do you think? (y/n) "
            
            sources = self._get_sources()
            if sources:
                return f"{acknowledgment}\n\nFor further reading:\n" + "\n".join(sources) + "\n\nWe may see this differently, and that's okay."
            
            # Nothing to offer, just acknowledge and move on
            self.agree()
            return self._advance() or "Let's explore the next point."
        
        # Default: neutral advance
        self.agree()
        return self._advance()
    
    def _advance(self) -> str | None:
        """Advance to next statement.
        
        Returns:
            Next statement with prompt, or conclusion if done.
        """
        result = self._get_next_statement()
        
        if result is None:
            self.state.finished = True
            return str(self.argument.conclusion)
        
        premise_name, statement = result
        return f"{statement}\nWhat's your view? (y/n) "


class MaieuticPolicy(BasePolicy):
    """Maieutic (guided-discovery) method — leads user to the argument via questions.

    Best for: self-directed learning, philosophy seminars, coaching contexts.
    """

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
        super().__init__(argument)
        self.question_count: int = 0

    def handle_input(self, user_input: str) -> str | None:
        """Respond with a topic-aware question based on user input."""
        user_lower = user_input.lower().strip()

        five_w = self._check_five_w(user_lower)
        if five_w:
            return five_w

        is_agreement = any(word in user_lower for word in ['yes', 'agree', 'yep', 'true'])
        is_disagreement = any(word in user_lower for word in ['no', 'disagree', 'false', 'wrong'])

        if is_disagreement:
            templates = self.DISAGREEMENT_QUESTIONS
            template = random.choice(templates)
            self.question_count += 1
            return template.format(topic=self.argument.name.replace("_", " "))

        if is_agreement:
            # After agreement, present the next premise statement
            self.agree()
            next_stmt = self._get_next_statement()
            if next_stmt:
                _, statement = next_stmt
                return f"{statement}\nDo you agree? (y/n) "
            self.state.finished = True
            return str(self.argument.conclusion)

        # Neutral — ask one intro question, then present a statement
        if self.question_count == 0:
            template = random.choice(self.INTRO_QUESTIONS)
            topic = self.argument.name.replace("_", " ")
            self.question_count += 1
            return template.format(topic=topic)

        next_stmt = self._get_next_statement()
        if next_stmt:
            _, statement = next_stmt
            self.question_count = 0
            return f"{statement}\nDo you agree? (y/n) "
        self.state.finished = True
        return str(self.argument.conclusion)

    def start(self) -> str:
        """Start with an open topic question."""
        topic = self.argument.name.replace("_", " ")
        return f"Let's explore: {topic}. What's your initial perspective?"


class SkepticPolicy(BasePolicy):
    """Skeptical debater — challenges every claim.

    Best for: stress-testing arguments, adversarial review.
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
        """Challenge the user's position."""
        user_lower = user_input.lower().strip()

        five_w = self._check_five_w(user_lower)
        if five_w:
            return five_w

        if any(word in user_lower for word in ['yes', 'agree', 'yep']):
            return random.choice(self.CHALLENGE_PHRASES)

        if any(word in user_lower for word in ['no', 'disagree']):
            next_stmt = self._get_next_statement()
            if next_stmt:
                _, statement = next_stmt
                prefix = random.choice(self.COUNTER_PHRASES)
                return f"{prefix}{statement}"

        return "I need more convincing. What specific evidence can you provide?"


class TeacherPolicy(BasePolicy):
    """Patient educator — explains with examples.

    Best for: clarity-focused teaching, onboarding, newcomers to a topic.
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
        super().__init__(argument)
        self.explaining = False

    def handle_input(self, user_input: str) -> str | None:
        """Provide educational response."""
        user_lower = user_input.lower().strip()

        five_w = self._check_five_w(user_lower)
        if five_w:
            return five_w

        if '?' in user_input:
            return random.choice(self.TRANSITION_PHRASES) + " " + self._get_explanation()

        if any(word in user_lower for word in ['yes', 'agree', 'understand']):
            return self._reinforce_concept()

        if any(word in user_lower for word in ['no', 'disagree', 'confused']):
            return self._clarify_misconception()

        return self._teach_with_example()

    def _get_explanation(self) -> str:
        next_stmt = self._get_next_statement()
        if next_stmt:
            return next_stmt[1]
        return self.argument.conclusion

    def _reinforce_concept(self) -> str:
        explanation = self._get_explanation()
        summary = random.choice(self.SUMMARY_PHRASES)
        return f"{summary}{explanation}"

    def _clarify_misconception(self) -> str:
        next_stmt = self._get_next_statement()
        if next_stmt:
            _, statement = next_stmt
            return f"Let me clarify: {statement}"
        return "Let me rephrase that more clearly."

    def _teach_with_example(self) -> str:
        next_stmt = self._get_next_statement()
        if next_stmt:
            _, statement = next_stmt
            example_intro = random.choice(self.EXAMPLE_INTROS)
            return f"{example_intro}{statement}"
        return self.argument.conclusion


class DebaterPolicy(BasePolicy):
    """Aggressive debater — presents strong counterarguments.

    Best for: debate practice, adversarial argumentation training.
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
        super().__init__(argument)
        self.points_made: int = 0

    def handle_input(self, user_input: str) -> str | None:
        """Present counterarguments."""
        user_lower = user_input.lower().strip()

        five_w = self._check_five_w(user_lower)
        if five_w:
            return five_w

        if len(user_lower) > 10:
            attack = random.choice(self.ATTACK_PHRASES)
            next_stmt = self._get_next_statement()
            if next_stmt:
                _, counter = next_stmt
                return f"{attack} {counter}"
            return attack

        if any(word in user_lower for word in ['yes', 'agree', 'fine']):
            return random.choice(self.DEFENSE_PHRASES)

        if any(word in user_lower for word in ['no', 'disagree']):
            next_stmt = self._get_next_statement()
            if next_stmt:
                _, statement = next_stmt
                return f"Consider this: {statement}"

        next_stmt = self._get_next_statement()
        if next_stmt:
            return next_stmt[1]

        return self.argument.conclusion


class MinimalistPolicy(BasePolicy):
    """Concise communicator — brief and direct.

    Best for: quick debates, mobile interfaces, low-bandwidth interactions.
    """

    BRIEF_AGREE = ["Agreed.", "True.", "Correct.", "Yes.", "Right."]
    BRIEF_DISAGREE = ["Disagree.", "Wrong.", "Incorrect.", "No.", "False."]
    BRIEF_STATEMENTS = ["Here's why:", "Evidence:", "Fact:", "Reality:", "Truth:"]

    def handle_input(self, user_input: str) -> str | None:
        """Respond briefly."""
        user_lower = user_input.lower().strip()

        five_w = self._check_five_w(user_lower)
        if five_w:
            return five_w[:100] + ("..." if len(five_w) > 100 else "")

        if any(word in user_lower for word in ['yes', 'agree', 'yep']):
            return random.choice(self.BRIEF_AGREE)

        if any(word in user_lower for word in ['no', 'disagree', 'nah']):
            next_stmt = self._get_next_statement()
            if next_stmt:
                _, stmt = next_stmt
                brief = stmt[:50] + ("..." if len(stmt) > 50 else "")
                return f"{random.choice(self.BRIEF_STATEMENTS)} {brief}"
            return random.choice(self.BRIEF_DISAGREE)

        next_stmt = self._get_next_statement()
        if next_stmt:
            _, stmt = next_stmt
            return stmt[:100] + ("..." if len(stmt) > 100 else "")

        return self.argument.conclusion[:100]


class AdaptivePolicy(BasePolicy):
    """Meta-policy that switches strategy based on engagement signals.

    Starts with *initial_policy* (default: ``KnowItAllPolicy``).  After
    *switch_threshold* consecutive disagreements it swaps to
    *fallback_policy* (default: ``ExploratoryPolicy``) for the remainder
    of the session.  State (spoken premises, transcript) is transferred
    seamlessly so no content is repeated.

    Best for: public-facing deployments where audience sentiment is unknown.
    """

    def __init__(
        self,
        argument: Argument,
        initial_policy: type[BasePolicy] = KnowItAllPolicy,
        fallback_policy: type[BasePolicy] = ExploratoryPolicy,
        switch_threshold: int = 3,
    ) -> None:
        """Initialise AdaptivePolicy.

        Args:
            argument: Argument to present.
            initial_policy: Policy class to start with.
            fallback_policy: Policy class to switch to after threshold reached.
            switch_threshold: Number of consecutive disagreements before switching.
        """
        super().__init__(argument)
        self._initial_cls = initial_policy
        self._fallback_cls = fallback_policy
        self.switch_threshold = switch_threshold
        self._consecutive_disagree: int = 0
        self._switched: bool = False
        self._active: BasePolicy = initial_policy(argument)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sync_state(self) -> None:
        """Copy shared session state from this policy into the active delegate."""
        self._active.state.spoken_premises = self.state.spoken_premises
        self._active.state.spoken_statements = self.state.spoken_statements
        self._active.state.current_premise = self.state.current_premise
        self._active.state.user_agrees = self.state.user_agrees
        self._active.state.finished = self.state.finished
        self._active.state.challenge_count = self.state.challenge_count
        self._active.state.transcript = self.state.transcript

    def _pull_state(self) -> None:
        """Copy shared session state back from the active delegate."""
        self.state.spoken_premises = self._active.state.spoken_premises
        self.state.spoken_statements = self._active.state.spoken_statements
        self.state.current_premise = self._active.state.current_premise
        self.state.user_agrees = self._active.state.user_agrees
        self.state.finished = self._active.state.finished
        self.state.challenge_count = self._active.state.challenge_count
        self.state.transcript = self._active.state.transcript

    def _maybe_switch(self, user_input: str) -> None:
        """Track disagreement count and switch policy when threshold hit."""
        if self._switched:
            return
        lower = user_input.lower()
        if any(w in lower for w in ("no", "disagree", "wrong", "false")):
            self._consecutive_disagree += 1
        else:
            self._consecutive_disagree = 0

        if self._consecutive_disagree >= self.switch_threshold:
            new_policy = self._fallback_cls(self.argument)
            self._sync_state()
            new_policy.state = self._active.state
            self._active = new_policy
            self._switched = True

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def switched(self) -> bool:
        """True once the fallback policy has been activated."""
        return self._switched

    @property
    def active_policy(self) -> BasePolicy:
        """The currently active delegate policy."""
        return self._active

    def start(self) -> str:
        """Start dialog, initialise active policy."""
        intro = super().start()
        self._active = self._initial_cls(self.argument)
        self._sync_state()
        self._consecutive_disagree = 0
        self._switched = False
        return intro

    def handle_input(self, user_input: str) -> str | None:
        """Delegate to active policy, switching if threshold reached."""
        self._maybe_switch(user_input)
        self._sync_state()
        response = self._active.handle_input(user_input)
        self._pull_state()
        return response


class WebhookPolicy(BasePolicy):
    """Policy that forwards every turn to an external HTTP endpoint.

    On each ``handle_input()`` call the policy POSTs a JSON payload to
    *webhook_url* and uses the returned text as the bot response.  If the
    request fails (network error, non-200 status) the *fallback_policy* is
    invoked instead so the conversation never stalls.

    Payload sent (POST, ``Content-Type: application/json``)::

        {
            "argument": "<argument name>",
            "user_input": "<user text>",
            "current_premise": "<premise name or null>",
            "transcript": [{"role": "bot"|"user", "text": "…"}, …]
        }

    Expected response (JSON)::

        {"response": "<bot reply text>"}

    Best for: hybrid LLM-enhanced deployments where structured fallback is
    required but natural language variety is desired at runtime.

    Args:
        argument: Argument to present.
        webhook_url: HTTP(S) endpoint that receives turn payloads.
        fallback_policy: Policy class used when webhook call fails.
        timeout: Request timeout in seconds (default 10).
    """

    def __init__(
        self,
        argument: Argument,
        webhook_url: str,
        fallback_policy: type[BasePolicy] = KnowItAllPolicy,
        timeout: float = 10.0,
    ) -> None:
        import urllib.request as _urllib
        super().__init__(argument)
        self.webhook_url = webhook_url
        self.timeout = timeout
        self._fallback = fallback_policy(argument)
        self._urllib = _urllib

    def _sync_fallback_state(self) -> None:
        """Mirror current state into the fallback policy."""
        self._fallback.state.spoken_premises = self.state.spoken_premises
        self._fallback.state.spoken_statements = self.state.spoken_statements
        self._fallback.state.current_premise = self.state.current_premise
        self._fallback.state.user_agrees = self.state.user_agrees
        self._fallback.state.finished = self.state.finished
        self._fallback.state.challenge_count = self.state.challenge_count

    def _call_webhook(self, user_input: str) -> str | None:
        """POST to webhook and return response text, or None on failure."""
        import json as _json
        payload = _json.dumps({
            "argument": self.argument.name,
            "user_input": user_input,
            "current_premise": self.state.current_premise,
            "transcript": [
                {"role": e.role, "text": e.text}
                for e in self.state.transcript
            ],
        }).encode()

        req = self._urllib.Request(
            self.webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._urllib.urlopen(req, timeout=self.timeout) as resp:
                if resp.status != 200:
                    return None
                body = _json.loads(resp.read())
                return body.get("response")
        except Exception:
            return None

    def handle_input(self, user_input: str) -> str | None:
        """Forward turn to webhook; fall back to local policy on failure."""
        response = self._call_webhook(user_input)
        if response is not None:
            return response
        # Webhook unavailable — delegate to fallback
        self._sync_fallback_state()
        result = self._fallback.handle_input(user_input)
        # Pull back any state changes made by fallback
        self.state.spoken_premises = self._fallback.state.spoken_premises
        self.state.spoken_statements = self._fallback.state.spoken_statements
        self.state.current_premise = self._fallback.state.current_premise
        self.state.user_agrees = self._fallback.state.user_agrees
        self.state.finished = self._fallback.state.finished
        self.state.challenge_count = self._fallback.state.challenge_count
        return result


# Registry mapping lowercase names to policy classes.
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
    "adaptive": AdaptivePolicy,
    # WebhookPolicy intentionally excluded — requires webhook_url constructor arg
}


def get_policy(name: str, argument: Argument) -> BasePolicy:
    """Get a policy instance by name.

    Args:
        name: Policy name (case-insensitive).
        argument: Argument to apply the policy to.

    Returns:
        Policy instance.

    Raises:
        InvalidPolicyError: If policy name is not recognized.
    """
    name_lower = name.lower().strip()
    if name_lower not in POLICY_REGISTRY:
        available = ", ".join(POLICY_REGISTRY.keys())
        raise InvalidPolicyError(f"Unknown policy: {name_lower!r}. Available: {available}")
    return POLICY_REGISTRY[name_lower](argument)
