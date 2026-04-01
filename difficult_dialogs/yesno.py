"""Fuzzy yes/no detection for dialog input parsing.

Loads a yes/no solver via the ``opm.agents.yesno`` entry-point group.
The default plugin is ``ovos-solver-yes-no-plugin`` (a hard dependency).
Users can replace it with any compatible ``opm.agents.yesno`` plugin.

Entry-point group: ``opm.agents.yesno``
Default plugin:    ``ovos-solver-yes-no-plugin``
"""
from __future__ import annotations

import importlib.metadata
import logging
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
    eps = {
        ep.name: ep
        for ep in importlib.metadata.entry_points(group=_ENTRY_POINT_GROUP)
    }

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

    raise RuntimeError(
        f"No usable opm.agents.yesno plugin found. "
        f"Install the default: pip install ovos-solver-yes-no-plugin. "
        f"Available: {list(eps)}"
    )


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
