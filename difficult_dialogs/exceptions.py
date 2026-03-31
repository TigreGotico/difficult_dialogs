"""Package-level exceptions for difficult_dialogs.

Callers can catch these to distinguish framework errors from generic Python
exceptions without importing internal modules.
"""
from __future__ import annotations


class DifficultDialogsError(Exception):
    """Base exception for all difficult_dialogs errors."""


class ArgumentLoadError(DifficultDialogsError):
    """Raised when an argument directory cannot be loaded or parsed."""


class ArgumentSaveError(DifficultDialogsError):
    """Raised when an argument cannot be saved to disk."""


class InvalidPolicyError(DifficultDialogsError):
    """Raised when an unknown or invalid policy name is requested."""


class MissingStatementError(DifficultDialogsError):
    """Raised when a premise has no statements but at least one is required."""


# ---------------------------------------------------------------------------
# Legacy aliases — kept so any existing catch-sites still compile.
# ---------------------------------------------------------------------------
DifficultDialogsException = DifficultDialogsError  # old base name
MissingStatementException = MissingStatementError
UnrecognizedArgumentFormat = ArgumentLoadError
BadArgumentJson = ArgumentLoadError
