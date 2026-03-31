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
    KnowItAllPolicy,
    SilentPolicy,
    SocraticPolicy,
    DebatePolicy,
    ExploratoryPolicy,
    PolicyState,
)
from difficult_dialogs.policies import (
    MaieuticPolicy,
    SkepticPolicy,
    TeacherPolicy,
    DebaterPolicy,
    MinimalistPolicy,
    POLICY_REGISTRY,
    get_policy,
)

__version__ = "0.5.0"
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
    # Policy registry
    "POLICY_REGISTRY",
    "get_policy",
]
