"""Fuzzy yes/no detection for dialog input parsing.

Loads a yes/no solver via the ``opm.agents.yesno`` entry-point group when
available.  Falls back to a built-in regex solver so the library works
without any external dependencies.

Default plugin: ``ovos-solver-yes-no-plugin`` (optional)
"""
from __future__ import annotations

import importlib.metadata
import logging
import re
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)

_DEFAULT_PLUGIN = "ovos-solver-yes-no-plugin"
_ENTRY_POINT_GROUPS = ("opm.agents.yesno",)


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
# Built-in regex fallback — works without any external dependency
# ---------------------------------------------------------------------------

_YES_WORDS = frozenset({
    "yes", "yeah", "yep", "yup", "agree", "agreed", "correct",
    "affirmative", "true", "ok", "okay", "sure", "certainly",
    "absolutely", "right", "indeed", "of course",
})
_NO_WORDS = frozenset({
    "no", "nope", "nah", "disagree", "incorrect", "false",
    "negative", "wrong", "never",
})
_NEGATION_RE = re.compile(
    r"\b(?:don't|dont|do not|doesn't|doesnt|does not|"
    r"not|n't|never|no)\b",
    re.IGNORECASE,
)


class _BuiltinYesNoSolver:
    """Minimal English-only yes/no solver using regex heuristics.

    Two-pass approach: first check for negation markers that flip polarity,
    then scan for yes/no keywords right-to-left (last keyword wins).
    """

    def match_yes_or_no(self, text: str, lang: str = "en-US") -> bool | None:
        tokens = re.findall(r"[a-z']+", text.lower())
        if not tokens:
            return None

        # Collect yes/no keyword hits with positions
        result: bool | None = None
        yes_hit = False
        no_hit = False
        for tok in tokens:
            if tok in _YES_WORDS:
                result = True
                yes_hit = True
            elif tok in _NO_WORDS:
                result = False
                no_hit = True

        # Only apply negation flip when a positive keyword co-occurs
        # with a negation marker (e.g. "I don't agree").
        # Don't flip when the only keyword IS the negation ("no", "never").
        if yes_hit and not no_hit and bool(_NEGATION_RE.search(text)):
            result = False

        return result


# ---------------------------------------------------------------------------
# Plugin loader
# ---------------------------------------------------------------------------

def _load_solver(plugin_name: str = _DEFAULT_PLUGIN) -> YesNoSolverProtocol:
    """Load a yes/no solver from the ``opm.agents.yesno`` entry-point group.

    Tries *plugin_name* first, then any other registered plugin.

    Args:
        plugin_name: Entry-point name to prefer (default: ``ovos-solver-yes-no-plugin``).

    Returns:
        An instantiated solver satisfying :class:`YesNoSolverProtocol`.

    Raises:
        RuntimeError: If no compatible plugin can be loaded.
    """
    eps: dict[str, importlib.metadata.EntryPoint] = {}
    for group in _ENTRY_POINT_GROUPS:
        for ep in importlib.metadata.entry_points(group=group):
            eps.setdefault(ep.name, ep)  # first group wins on name collision

    for name in (plugin_name, *eps.keys()):
        if name not in eps:
            continue
        try:
            cls = eps[name].load()
            instance = cls()
            if callable(getattr(instance, "match_yes_or_no", None)):
                logger.debug("difficult_dialogs: loaded yes/no solver '%s'", name)
                return instance
        except Exception as exc:
            logger.warning(
                "difficult_dialogs: failed to load yes/no solver '%s': %s",
                name, exc,
            )

    logger.info(
        "difficult_dialogs: no OPM yes/no plugin found; using built-in regex solver. "
        "Install ovos-solver-yes-no-plugin for better accuracy."
    )
    return _BuiltinYesNoSolver()


# Module-level singleton — loaded once on first use
_solver: YesNoSolverProtocol | None = None
_yesno_plugin: str = _DEFAULT_PLUGIN


def _get_solver() -> YesNoSolverProtocol:
    global _solver
    if _solver is None:
        _solver = _load_solver(_yesno_plugin)
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


def configure(yesno_plugin: str = _DEFAULT_PLUGIN) -> None:
    """Choose which ``opm.agents.yesno`` plugin to use.

    Must be called before the first ``parse_yes_no`` call (or after
    ``set_solver(None)`` to force a reload).

    Args:
        yesno_plugin: Entry-point name, e.g. ``"ovos-solver-yes-no-plugin"``.
    """
    global _yesno_plugin, _solver
    _yesno_plugin = yesno_plugin
    _solver = None  # force reload on next use


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_solvers() -> dict[str, str]:
    """Return a mapping of entry-point name → entry-point value for all registered yes/no solvers.

    Returns:
        Dict of ``{name: dotted.path.ClassName}`` for every plugin found in
        :data:`_ENTRY_POINT_GROUPS`.  Returns an empty dict when none are installed.

    Example::

        from difficult_dialogs.yesno import list_solvers
        print(list_solvers())
        # {'ovos-solver-yes-no-plugin': 'ovos_yes_no_solver:YesNoSolver'}
    """
    import importlib.metadata as _meta

    result: dict[str, str] = {}
    for group in _ENTRY_POINT_GROUPS:
        for ep in _meta.entry_points(group=group):
            result.setdefault(ep.name, ep.value)
    return result


def parse_yes_no(text: str, lang: str = "en-US") -> bool | None:
    """Parse natural-language text as agreement, disagreement, or neither.

    Delegates to the active ``opm.agents.yesno`` plugin.

    Args:
        text: Raw user input string.
        lang: BCP-47 language code (e.g. ``"en-US"``, ``"pt-BR"``).

    Returns:
        ``True``  — user agrees / yes.
        ``False`` — user disagrees / no.
        ``None``  — neutral / ambiguous; caller decides.
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
