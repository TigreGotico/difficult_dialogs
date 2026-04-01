"""Shared pytest fixtures.

Installs a lightweight mock yes/no solver for the entire test session so
that tests never depend on ovos-solver-yes-no-plugin being loadable in
the project venv. The mock returns True for "yes"/"agree", False for
"no"/"disagree", and None for everything else — matching the real plugin
behaviour for basic English inputs.
"""
import re
import pytest
import difficult_dialogs.yesno as yesno_module


_YES = frozenset({"yes", "yeah", "yep", "yup", "agree", "agreed", "correct",
                   "affirmative", "true", "ok", "okay", "sure", "certainly"})
_NO  = frozenset({"no", "nope", "nah", "disagree", "incorrect", "false",
                   "negative", "wrong"})


class _TestYesNoSolver:
    """Minimal English yes/no solver for the test suite."""

    def match_yes_or_no(self, text: str, lang: str = "en-US") -> bool | None:
        tokens = re.findall(r"[a-z']+", text.lower())
        result: bool | None = None
        best = -1
        for i, tok in enumerate(tokens):
            if tok in _YES and i >= best:
                result = True
                best = i
            elif tok in _NO and i >= best:
                result = False
                best = i
        return result


@pytest.fixture(autouse=True, scope="session")
def mock_yesno_solver():
    """Replace the OPM yes/no solver with a test-local implementation."""
    original = yesno_module._solver
    yesno_module._solver = _TestYesNoSolver()
    yield
    yesno_module._solver = original
