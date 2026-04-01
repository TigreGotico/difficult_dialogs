"""Choice module — multiple-choice input for structured dialog.

Provides ``ChoiceOption``, a pluggable ``ChoiceSolverProtocol``, and the
top-level ``parse_choice()`` helper used by policies to map free-form user
input (or a single letter) to a labelled option.

The default solver is purely offline: it matches the user's input against
option labels (A/B/C…) and option text prefixes — no LLM required.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class ChoiceOption:
    """A single option in a multiple-choice question.

    Attributes:
        label: Short identifier presented to the user, e.g. ``"A"``.
        text: Human-readable description of the option.
        outcome: Semantic outcome — one of ``"agree"``, ``"disagree"``,
            ``"clarify"``, or ``"skip"``.
        next_premise: Optional name of the premise to jump to when this
            option is selected.  ``None`` means follow the default graph
            edge (``on_agree`` / ``on_disagree``) or linear order.
    """

    label: str
    text: str
    outcome: str = "agree"
    next_premise: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        """Serialise to a JSON-safe dict."""
        return {
            "label": self.label,
            "text": self.text,
            "outcome": self.outcome,
            "next_premise": self.next_premise,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | None]) -> ChoiceOption:
        """Restore from a plain dict."""
        return cls(
            label=str(data["label"]),
            text=str(data["text"]),
            outcome=str(data.get("outcome", "agree")),
            next_premise=data.get("next_premise") or None,  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# Solver protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class ChoiceSolverProtocol(Protocol):
    """Protocol for pluggable choice-matching backends.

    Implementations may use fuzzy matching, embeddings, or LLM classification.
    The default built-in solver uses label and prefix matching only.
    """

    def match_choice(
        self,
        text: str,
        options: list[ChoiceOption],
        lang: str,
    ) -> ChoiceOption | None:
        """Return the best matching option for *text*, or ``None``.

        Args:
            text: Raw user input.
            options: Available choices for the current premise.
            lang: BCP-47 language code (e.g. ``"en-US"``).

        Returns:
            The matched ``ChoiceOption``, or ``None`` if no match.
        """
        ...


# ---------------------------------------------------------------------------
# Default offline solver
# ---------------------------------------------------------------------------

class _DefaultChoiceSolver:
    """Offline label/prefix matcher — no external dependencies.

    Matching strategy (in order):
    1. Exact label match (case-insensitive, strips punctuation).
    2. Input starts with label (e.g. ``"a)"`` or ``"a."``)
    3. Input is a 1-based integer index (``"1"`` → option 0).
    4. Case-insensitive prefix of the option text.
    """

    def match_choice(
        self,
        text: str,
        options: list[ChoiceOption],
        lang: str,
    ) -> ChoiceOption | None:
        """Return the matched option or ``None``.

        Args:
            text: Raw user input.
            options: Available choices.
            lang: BCP-47 language code (unused in default solver).

        Returns:
            Matched ``ChoiceOption`` or ``None``.
        """
        normalised = text.strip().lower()

        # 1. Exact label match
        for opt in options:
            if normalised == opt.label.lower():
                return opt

        # 2. Input starts with label (e.g. "a)" / "a." / "a ")
        for opt in options:
            pattern = re.escape(opt.label.lower())
            if re.match(rf"^{pattern}[\s\.\)\:,]", normalised):
                return opt

        # 3. 1-based integer index
        if re.fullmatch(r"\d+", normalised):
            idx = int(normalised) - 1
            if 0 <= idx < len(options):
                return options[idx]

        # 4. Prefix of option text (≥ 3 chars)
        if len(normalised) >= 3:
            for opt in options:
                if opt.text.lower().startswith(normalised):
                    return opt

        return None


_DEFAULT_SOLVER = _DefaultChoiceSolver()


# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------

def parse_choice(
    text: str,
    options: list[ChoiceOption],
    lang: str = "en-US",
    solver: ChoiceSolverProtocol | None = None,
) -> ChoiceOption | None:
    """Map raw user input to a ``ChoiceOption``.

    Args:
        text: The user's raw reply.
        options: Ordered list of available choices.
        lang: BCP-47 language code passed through to the solver.
        solver: Optional custom solver.  Defaults to the offline
            label/prefix matcher.

    Returns:
        The matched ``ChoiceOption``, or ``None`` if no match.
    """
    active = solver if solver is not None else _DEFAULT_SOLVER
    return active.match_choice(text, options, lang)


# ---------------------------------------------------------------------------
# File format parser
# ---------------------------------------------------------------------------

# Default outcome per positional label when no outcome keyword is present.
_POSITIONAL_OUTCOMES: dict[str, str] = {
    "A": "agree",
    "B": "agree",
    "C": "disagree",
    "D": "clarify",
    "E": "skip",
}

_OUTCOME_KEYWORDS: set[str] = {"agree", "disagree", "clarify", "skip"}


def parse_choices_file(text: str) -> list[ChoiceOption]:
    """Parse the contents of a ``.choices`` file into a list of options.

    File format (one option per non-empty line)::

        A) I agree completely -> next_premise
        B) I agree with reservations
        C) I disagree [disagree]
        D) I need more context [clarify]

    Rules:

    * Label is the word before the first ``)``.  Auto-assigned (A, B, C…)
      if the line has no ``)``.
    * ``-> premise_name`` at the end sets ``next_premise``.
    * ``[outcome]`` at the end (after ``->`` is stripped) sets ``outcome``.
    * If neither is present the outcome defaults to the positional default
      from ``_POSITIONAL_OUTCOMES`` (A=agree, B=agree, C=disagree, D=clarify).

    Args:
        text: Raw file contents.

    Returns:
        List of ``ChoiceOption`` instances.
    """
    options: list[ChoiceOption] = []
    auto_labels = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        next_premise: str | None = None
        outcome: str | None = None

        # Extract -> next_premise
        arrow_match = re.search(r"\s*->\s*(\S+)\s*$", line)
        if arrow_match:
            next_premise = arrow_match.group(1)
            line = line[: arrow_match.start()]

        # Extract [outcome]
        bracket_match = re.search(r"\s*\[(\w+)\]\s*$", line)
        if bracket_match:
            word = bracket_match.group(1).lower()
            if word in _OUTCOME_KEYWORDS:
                outcome = word
                line = line[: bracket_match.start()]

        # Extract label
        paren_match = re.match(r"^([A-Za-z0-9]+)\s*\)\s*(.+)$", line)
        if paren_match:
            label = paren_match.group(1).upper()
            text_part = paren_match.group(2).strip()
        else:
            label = auto_labels[len(options)] if len(options) < len(auto_labels) else str(len(options) + 1)
            text_part = line.strip()

        if not outcome:
            outcome = _POSITIONAL_OUTCOMES.get(label, "agree")

        options.append(ChoiceOption(
            label=label,
            text=text_part,
            outcome=outcome,
            next_premise=next_premise,
        ))

    return options
