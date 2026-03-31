"""Fuzzy yes/no detection for dialog input parsing.

Recognises agreement and disagreement from natural-language responses so
callers are not limited to bare "y" / "n" input.

Inspired by the word-list approach used in ovos-solver-YesNo-plugin.
No external dependencies required.
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Word lists (English)
# ---------------------------------------------------------------------------

_YES_WORDS: frozenset[str] = frozenset({
    "yes", "yeah", "yep", "yup", "yea",
    "correct", "confirmed", "confirm",
    "affirmative", "agree", "agreed",
    "indeed", "absolutely", "exactly",
    "right", "true", "ok", "okay",
})

_NO_WORDS: frozenset[str] = frozenset({
    "no", "nope", "nah", "nay",
    "negative", "negatory",
    "disagree", "disagreed",
    "incorrect", "false",
})

# Weak / hedged yes — only match when nothing stronger was found
_NEUTRAL_YES: frozenset[str] = frozenset({
    "sure", "surely", "certainly", "please",
    "obviously", "definitely", "course",
    "fine", "alright",
})

# Weak / hedged no — only match when nothing stronger was found
_NEUTRAL_NO: frozenset[str] = frozenset({
    "wrong", "mistaken", "mistake",
    "lie", "lying", "untrue",
    "inappropriate", "undesirable", "unwanted",
})

# Negation words that can flip a following neutral-no word into yes
_NEGATIONS: frozenset[str] = frozenset({
    "not", "don't", "do not", "doesn't",
    "isn't", "aren't", "wasn't", "weren't",
})


def _tokenize(text: str) -> list[str]:
    """Lower-case and split on word boundaries."""
    return re.findall(r"[a-z']+", text.lower())


def _find_last(tokens: list[str], wordset: frozenset[str]) -> int:
    """Return the index of the *last* token that appears in *wordset*, or -1."""
    result = -1
    for i, tok in enumerate(tokens):
        if tok in wordset:
            result = i
    return result


def parse_yes_no(text: str) -> bool | None:
    """Parse natural-language text as agreement, disagreement, or neither.

    Args:
        text: Raw user input string.

    Returns:
        ``True``  — user agrees / yes.
        ``False`` — user disagrees / no.
        ``None``  — neutral / ambiguous, caller should decide.

    Examples::

        >>> parse_yes_no("yeah that sounds right")
        True
        >>> parse_yes_no("nope I disagree")
        False
        >>> parse_yes_no("I don't know")
        None
        >>> parse_yes_no("sure")
        True
        >>> parse_yes_no("that's wrong")
        False
    """
    tokens = _tokenize(text)

    yes_idx = _find_last(tokens, _YES_WORDS)
    no_idx = _find_last(tokens, _NO_WORDS)

    def _has_negation_before(idx: int) -> bool:
        """Return True if a negation token immediately precedes *idx*."""
        if idx > 0 and tokens[idx - 1] in _NEGATIONS:
            return True
        if idx >= 2 and " ".join(tokens[idx - 2: idx]) in _NEGATIONS:
            return True
        return False

    # Strong signal — whichever comes *last* wins (handles "yes… wait, no")
    if yes_idx != -1 or no_idx != -1:
        if no_idx > yes_idx:
            # "not wrong" / "not disagree" → double negative → yes
            return True if _has_negation_before(no_idx) else False
        # yes-word is last — check for negation ("don't agree") → no
        return False if _has_negation_before(yes_idx) else True

    # Fall back to weak signals
    neutral_yes_idx = _find_last(tokens, _NEUTRAL_YES)
    neutral_no_idx = _find_last(tokens, _NEUTRAL_NO)

    if neutral_yes_idx != -1 or neutral_no_idx != -1:
        if neutral_no_idx > neutral_yes_idx:
            # "not wrong" with neutral_no → yes
            return True if _has_negation_before(neutral_no_idx) else False
        return True

    return None


def is_agreement(text: str, default: bool = True) -> bool:
    """Return ``True`` if *text* expresses agreement.

    Args:
        text: Raw user input.
        default: Value to return when the intent is ambiguous.
    """
    result = parse_yes_no(text)
    if result is None:
        return default
    return result


def is_disagreement(text: str, default: bool = False) -> bool:
    """Return ``True`` if *text* expresses disagreement.

    Args:
        text: Raw user input.
        default: Value to return when the intent is ambiguous.
    """
    result = parse_yes_no(text)
    if result is None:
        return default
    return not result
