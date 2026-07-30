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
    CooperativePolicy,
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
    LLMEnhancedPolicy,
    MultiArgumentPolicy,
    MultiChoicePolicy,
    PolicyState,
    POLICY_REGISTRY,
    get_policy,
)

from difficult_dialogs.choices import (
    ChoiceOption,
    ChoiceSolverProtocol,
    parse_choice,
    parse_choices_file,
    set_solver as set_choice_solver,
    configure as configure_choice_solver,
    list_solvers as list_choice_solvers,
)
from difficult_dialogs.yesno import parse_yes_no, is_agreement, is_disagreement, set_solver, configure, list_solvers
from difficult_dialogs.library import ArgumentLibrary, SearchResult
from difficult_dialogs.builder import ArgumentBuilder, PremiseBuilder
from difficult_dialogs.validators import (
    ArgumentValidator,
    ValidationResult,
    ValidationSeverity,
    ValidationIssue,
)
from difficult_dialogs.export.transcript import (
    export_transcript_to_markdown,
    export_transcript_to_json,
)
from difficult_dialogs.export.csv import export_to_csv
from difficult_dialogs.export.graph import to_mermaid, to_dot, to_graph_json
from difficult_dialogs.graph import GraphData, GraphNode, GraphEdge
from difficult_dialogs.llm import ArgumentGenerator, LLMEnhancer, LLMClient
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
    "LLMEnhancedPolicy",
    "MultiArgumentPolicy",
    "MultiChoicePolicy",
    "CooperativePolicy",
    # Graph visualization
    "GraphData",
    "GraphNode",
    "GraphEdge",
    "to_mermaid",
    "to_dot",
    "to_graph_json",
    # Choices
    "ChoiceOption",
    "ChoiceSolverProtocol",
    "parse_choice",
    "parse_choices_file",
    "set_choice_solver",
    "configure_choice_solver",
    "list_choice_solvers",
    # Yes/no parsing
    "parse_yes_no",
    "is_agreement",
    "is_disagreement",
    "set_solver",
    "configure",
    "list_solvers",
    # Builder
    "ArgumentBuilder",
    "PremiseBuilder",
    # Library / search
    "ArgumentLibrary",
    "SearchResult",
    # Policy registry
    "POLICY_REGISTRY",
    "get_policy",
    # Validation
    "ArgumentValidator",
    "ValidationResult",
    "ValidationSeverity",
    "ValidationIssue",
    # Transcript export
    "export_transcript_to_markdown",
    "export_transcript_to_json",
    # CSV export
    "export_to_csv",
    # LLM integration (optional)
    "ArgumentGenerator",
    "LLMEnhancer",
    "LLMClient",
]
