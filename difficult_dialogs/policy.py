"""Policy module - controls dialog flow and user interaction.

Policies decide how conversations progress through an argument's premises.
"""
from __future__ import annotations

import asyncio
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, AsyncGenerator, Generator

if TYPE_CHECKING:
    from difficult_dialogs.arguments import Argument


@dataclass
class PolicyState:
    """Tracks the current state of a dialog session."""
    spoken_premises: set[str] = field(default_factory=set)
    spoken_statements: set[str] = field(default_factory=set)
    current_premise: str | None = None
    user_agrees: bool = True
    finished: bool = False


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
        pass
    
    def start(self) -> str:
        """Start the dialog and return intro statement.
        
        Returns:
            Intro statement text.
        """
        self.state = PolicyState()
        return str(self.argument.intro)
    
    def end(self) -> str:
        """End the dialog and return conclusion.
        
        Returns:
            Conclusion statement text.
        """
        self.state.finished = True
        return str(self.argument.conclusion)
    
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
        ):
            if keyword in user_input and items:
                return random.choice(items)

        return None

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
            response = self.handle_input(user_input or "")
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
            response = self.handle_input(user_input)
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
        self._challenge_count: int = 0
    
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
            self._challenge_count = 0
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
            self._challenge_count += 1
            return f"{intro}{support}\n\nDo you still disagree? (y/n) "
        
        # No specific support - use generic challenge
        self._challenge_count += 1
        if self._challenge_count >= 2:
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
