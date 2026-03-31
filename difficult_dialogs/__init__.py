"""Difficult Dialogs - Structured argumentation framework.

Tools to guide conversations towards a certain objective using file-based
argument definitions and pluggable policy engines.
"""
from difficult_dialogs.exceptions import (
    DifficultDialogsError,
    ArgumentLoadError,
    ArgumentSaveError,
    InvalidPolicyError,
    MissingStatementError,
)
from difficult_dialogs.statements import Statement
from difficult_dialogs.premises import Premise
from difficult_dialogs.arguments import Argument
from difficult_dialogs.policy import (
    BasePolicy,
    TranscriptEntry,
    KnowItAllPolicy,
    SilentPolicy,
    SocraticPolicy,
    DebatePolicy,
    ExploratoryPolicy,
    MaieuticPolicy,
    SkepticPolicy,
    TeacherPolicy,
    DebaterPolicy,
    MinimalistPolicy,
    AdaptivePolicy,
    WebhookPolicy,
    PolicyState,
    POLICY_REGISTRY,
    get_policy,
)

from difficult_dialogs.library import ArgumentLibrary, SearchResult
from difficult_dialogs.version import __version__
__all__ = [
    # Exceptions
    "DifficultDialogsError",
    "ArgumentLoadError",
    "ArgumentSaveError",
    "InvalidPolicyError",
    "MissingStatementError",
    # Core data model
    "Statement",
    "Premise",
    "Argument",
    # Policy base + state
    "BasePolicy",
    "PolicyState",
    "TranscriptEntry",
    # Built-in policies
    "KnowItAllPolicy",
    "SilentPolicy",
    "SocraticPolicy",
    "DebatePolicy",
    "ExploratoryPolicy",
    "MaieuticPolicy",
    "SkepticPolicy",
    "TeacherPolicy",
    "DebaterPolicy",
    "MinimalistPolicy",
    "AdaptivePolicy",
    "WebhookPolicy",
    # Library / search
    "ArgumentLibrary",
    "SearchResult",
    # Policy registry
    "POLICY_REGISTRY",
    "get_policy",
]
