"""Fuzzy yes/no detection for dialog input parsing.

Loads a yes/no solver via the ``opm.agents.yesno`` entry-point group so that
users can plug in any compatible solver (multilingual, LLM-backed, etc.).

The default solver is ``ovos-solver-yes-no-plugin``.  If the entry-point
cannot be loaded a minimal built-in fallback is used so the library never
hard-crashes on import.

Entry-point group: ``opm.agents.yesno``
Default plugin:    ``ovos-solver-yes-no-plugin``
"""
from __future__ import annotations

import importlib.metadata
import logging
import re
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)

_DEFAULT_PLUGIN = "ovos-solver-yes-no-plugin"
_ENTRY_POINT_GROUP = "opm.agents.yesno"


# ---------------------------------------------------------------------------
# Protocol — any object with match_yes_or_no(text, lang) → bool | None
# ---------------------------------------------------------------------------

@runtime_checkable
class YesNoSolverProtocol(Protocol):
    """Minimal interface required by this module."""

    def match_yes_or_no(self, text: str, lang: str) -> bool | None:
        """Return True (yes), False (no), or None (ambiguous)."""
        ...


# ---------------------------------------------------------------------------
# Built-in fallback (English only, zero external deps)
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

_NEUTRAL_YES: frozenset[str] = frozenset({
    "sure", "surely", "certainly", "please",
    "obviously", "definitely", "course",
    "fine", "alright",
})

_NEUTRAL_NO: frozenset[str] = frozenset({
    "wrong", "mistaken", "mistake",
    "lie", "lying", "untrue",
    "inappropriate", "undesirable", "unwanted",
})

_NEGATIONS: frozenset[str] = frozenset({
    "not", "don't", "do not", "doesn't",
    "isn't", "aren't", "wasn't", "weren't",
})


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z']+", text.lower())


def _find_last(tokens: list[str], wordset: frozenset[str]) -> int:
    result = -1
    for i, tok in enumerate(tokens):
        if tok in wordset:
            result = i
    return result


class _BuiltinYesNoSolver:
    """English-only fallback — used when the OPM plugin cannot be loaded."""

    def match_yes_or_no(self, text: str, lang: str = "en-US") -> bool | None:  # noqa: ARG002
        tokens = _tokenize(text)

        yes_idx = _find_last(tokens, _YES_WORDS)
        no_idx = _find_last(tokens, _NO_WORDS)

        def _negated(idx: int) -> bool:
            if idx > 0 and tokens[idx - 1] in _NEGATIONS:
                return True
            if idx >= 2 and " ".join(tokens[idx - 2: idx]) in _NEGATIONS:
                return True
            return False

        if yes_idx != -1 or no_idx != -1:
            if no_idx > yes_idx:
                return True if _negated(no_idx) else False
            return False if _negated(yes_idx) else True

        neutral_yes_idx = _find_last(tokens, _NEUTRAL_YES)
        neutral_no_idx = _find_last(tokens, _NEUTRAL_NO)

        if neutral_yes_idx != -1 or neutral_no_idx != -1:
            if neutral_no_idx > neutral_yes_idx:
                return True if _negated(neutral_no_idx) else False
            return True

        return None


# ---------------------------------------------------------------------------
# Plugin loader
# ---------------------------------------------------------------------------

def _import_default_solver() -> YesNoSolverProtocol | None:
    """Import ``ovos_yes_no_solver.YesNoSolver`` directly (hard dep).

    Separated into its own function so tests can monkeypatch it.

    Returns:
        An instantiated ``YesNoSolver``, or ``None`` on failure.
    """
    try:
        from ovos_yes_no_solver import YesNoSolver  # type: ignore[import-untyped]
        instance = YesNoSolver()
        if isinstance(instance, YesNoSolverProtocol):
            logger.debug("difficult_dialogs: loaded YesNoSolver via direct import")
            return instance
    except Exception as exc:
        logger.warning("difficult_dialogs: direct import of YesNoSolver failed: %s", exc)
    return None


def _load_solver(plugin_name: str = _DEFAULT_PLUGIN) -> YesNoSolverProtocol:
    """Load a yes/no solver.

    Resolution order:

    1. Any plugin registered under the ``opm.agents.yesno`` entry-point group
       whose name matches *plugin_name*.
    2. Any other plugin in the same entry-point group.
    3. Direct import of ``ovos_yes_no_solver.YesNoSolver`` (the hard dependency).
    4. Built-in English-only fallback (no external deps).

    Args:
        plugin_name: Entry-point name to prefer.

    Returns:
        An instantiated solver satisfying :class:`YesNoSolverProtocol`.
    """
    eps = {
        ep.name: ep
        for ep in importlib.metadata.entry_points(group=_ENTRY_POINT_GROUP)
    }

    # 1 & 2 — entry-point discovery (allows user replacement)
    for name in (plugin_name, *eps.keys()):
        if name not in eps:
            continue
        try:
            cls = eps[name].load()
            instance = cls()
            if isinstance(instance, YesNoSolverProtocol):
                logger.debug("difficult_dialogs: loaded yes/no solver '%s'", name)
                return instance
        except Exception as exc:
            logger.warning(
                "difficult_dialogs: failed to load yes/no solver '%s': %s",
                name, exc,
            )

    # 3 — direct import of the bundled default dependency
    direct = _import_default_solver()
    if direct is not None:
        return direct

    # 4 — built-in fallback
    logger.debug(
        "difficult_dialogs: using built-in English yes/no fallback"
    )
    return _BuiltinYesNoSolver()


# Module-level singleton — loaded once on first import
_solver: YesNoSolverProtocol | None = None


def _get_solver() -> YesNoSolverProtocol:
    global _solver
    if _solver is None:
        _solver = _load_solver()
    return _solver


def set_solver(solver: YesNoSolverProtocol) -> None:
    """Replace the active yes/no solver at runtime.

    Args:
        solver: Any object implementing ``match_yes_or_no(text, lang)``.

    Example::

        from difficult_dialogs.yesno import set_solver
        from ovos_yes_no_solver import YesNoSolver
        set_solver(YesNoSolver())
    """
    global _solver
    _solver = solver


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_yes_no(text: str, lang: str = "en-US") -> bool | None:
    """Parse natural-language text as agreement, disagreement, or neither.

    Delegates to the active yes/no solver (default: ``ovos-solver-yes-no-plugin``).

    Args:
        text: Raw user input string.
        lang: BCP-47 language code (e.g. ``"en-US"``, ``"pt-BR"``).

    Returns:
        ``True``  — user agrees / yes.
        ``False`` — user disagrees / no.
        ``None``  — neutral / ambiguous; caller decides.

    Examples::

        >>> parse_yes_no("yeah that sounds right")
        True
        >>> parse_yes_no("nope I disagree")
        False
        >>> parse_yes_no("I don't know")
        None
    """
    return _get_solver().match_yes_or_no(text, lang)


def is_agreement(text: str, lang: str = "en-US", default: bool = True) -> bool:
    """Return ``True`` if *text* expresses agreement.

    Args:
        text: Raw user input.
        lang: BCP-47 language code.
        default: Value returned when intent is ambiguous.
    """
    result = parse_yes_no(text, lang)
    return default if result is None else result


def is_disagreement(text: str, lang: str = "en-US", default: bool = False) -> bool:
    """Return ``True`` if *text* expresses disagreement.

    Args:
        text: Raw user input.
        lang: BCP-47 language code.
        default: Value returned when intent is ambiguous.
    """
    result = parse_yes_no(text, lang)
    return default if result is None else not result
