"""Validation framework for argument quality assurance.

Provides comprehensive validation of argument structure, content quality,
and logical consistency.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from difficult_dialogs.arguments import Argument


class ValidationSeverity(Enum):
    """Severity level of a validation issue."""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


@dataclass
class ValidationResult:
    """Result of validating an argument."""
    passed: bool
    score: float  # 0.0 to 1.0
    issues: list[ValidationIssue] = field(default_factory=list)
    
    def add_issue(self, severity: ValidationSeverity, message: str, 
                  category: str = "general") -> None:
        """Add a validation issue."""
        self.issues.append(ValidationIssue(severity, message, category))
        if severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL):
            self.passed = False
    
    def __str__(self) -> str:
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status} (score: {self.score:.2f}) - {len(self.issues)} issues"


@dataclass
class ValidationIssue:
    """A single validation issue."""
    severity: ValidationSeverity
    message: str
    category: str
    
    def __str__(self) -> str:
        icons = {
            ValidationSeverity.INFO: "ℹ️",
            ValidationSeverity.WARNING: "⚠️",
            ValidationSeverity.ERROR: "❌",
            ValidationSeverity.CRITICAL: "🔴"
        }
        return f"{icons[self.severity]} [{self.category}] {self.message}"


class ArgumentValidator:
    """Validates arguments for quality and consistency."""
    
    # Minimum requirements
    MIN_PREMISES = 2
    MAX_PREMISES = 6
    MIN_STATEMENTS_PER_PREMISE = 1
    MAX_STATEMENTS_PER_PREMISE = 5
    MIN_INTRO_LENGTH = 50
    MIN_CONCLUSION_LENGTH = 50
    
    # Quality thresholds
    QUALITY_EXCELLENT = 0.9
    QUALITY_GOOD = 0.7
    QUALITY_FAIR = 0.5
    
    def __init__(self) -> None:
        """Initialize validator."""
        self.validators = [
            self._validate_structure,
            self._validate_premises,
            self._validate_content_quality,
            self._validate_logical_consistency,
            self._validate_sources,
            self._validate_five_ws,
        ]
    
    def validate(self, argument: Argument) -> ValidationResult:
        """Run all validators on an argument.
        
        Args:
            argument: Argument to validate.
            
        Returns:
            ValidationResult with pass/fail, score, and issues.
        """
        result = ValidationResult(passed=True, score=1.0)
        
        for validator in self.validators:
            validator(argument, result)
        
        # Calculate final score based on issues
        self._calculate_score(result)
        
        return result
    
    def _calculate_score(self, result: ValidationResult) -> None:
        """Calculate quality score based on issues."""
        deductions = {
            ValidationSeverity.CRITICAL: 0.3,
            ValidationSeverity.ERROR: 0.15,
            ValidationSeverity.WARNING: 0.05,
            ValidationSeverity.INFO: 0.0,
        }
        
        total_deduction = sum(
            deductions[issue.severity] for issue in result.issues
        )
        
        result.score = max(0.0, 1.0 - total_deduction)
        
        # Fail if score too low
        if result.score < self.QUALITY_FAIR:
            result.passed = False
    
    def _validate_structure(self, argument: Argument, 
                           result: ValidationResult) -> None:
        """Validate basic structure requirements."""
        # Check intro
        if not argument.intro:
            result.add_issue(ValidationSeverity.CRITICAL, 
                           "Intro is empty", "structure")
        elif len(argument.intro) < self.MIN_INTRO_LENGTH:
            result.add_issue(ValidationSeverity.WARNING,
                           f"Intro too short ({len(argument.intro)} chars)",
                           "structure")
        
        # Check conclusion
        if not argument.conclusion:
            result.add_issue(ValidationSeverity.CRITICAL,
                           "Conclusion is empty", "structure")
        elif len(argument.conclusion) < self.MIN_CONCLUSION_LENGTH:
            result.add_issue(ValidationSeverity.WARNING,
                           f"Conclusion too short ({len(argument.conclusion)} chars)",
                           "structure")
        
        # Check intro != conclusion
        if argument.intro.strip() == argument.conclusion.strip():
            result.add_issue(ValidationSeverity.ERROR,
                           "Intro and conclusion are identical",
                           "structure")
        
        # Check premise count
        premise_count = len(argument.premises)
        if premise_count < self.MIN_PREMISES:
            result.add_issue(ValidationSeverity.ERROR,
                           f"Too few premises ({premise_count}, min {self.MIN_PREMISES})",
                           "structure")
        elif premise_count > self.MAX_PREMISES:
            result.add_issue(ValidationSeverity.WARNING,
                           f"Many premises ({premise_count}, max recommended {self.MAX_PREMISES})",
                           "structure")
    
    def _validate_premises(self, argument: Argument,
                          result: ValidationResult) -> None:
        """Validate premise structure and content."""
        premise_names = []
        
        for premise in argument.premises:
            premise_names.append(premise.name)
            
            # Check name
            if not premise.name:
                result.add_issue(ValidationSeverity.ERROR,
                               "Premise has no name",
                               "premises")
            
            # Check statements
            stmt_count = len(premise.statements)
            if stmt_count < self.MIN_STATEMENTS_PER_PREMISE:
                result.add_issue(ValidationSeverity.ERROR,
                               f"Premise '{premise.name}' has no statements",
                               "premises")
            elif stmt_count > self.MAX_STATEMENTS_PER_PREMISE:
                result.add_issue(ValidationSeverity.WARNING,
                               f"Premise '{premise.name}' has many statements ({stmt_count})",
                               "premises")
            
            # Check for duplicate statements within premise
            statement_texts = [s.text for s in premise.statements]
            duplicates = [s for s in statement_texts 
                         if statement_texts.count(s) > 1]
            if duplicates:
                result.add_issue(ValidationSeverity.ERROR,
                               f"Duplicate statements in '{premise.name}'",
                               "premises")
            
            # Check description file content
            if premise.description and len(premise.description) < 20:
                result.add_issue(ValidationSeverity.INFO,
                               f"Premise '{premise.name}' has brief description",
                               "premises")
        
    def _validate_content_quality(self, argument: Argument,
                                  result: ValidationResult) -> None:
        """Validate content quality metrics."""
        # Check for very short statements
        for premise in argument.premises:
            for stmt in premise.statements:
                if len(stmt.text) < 20:
                    result.add_issue(ValidationSeverity.INFO,
                                   f"Very short statement in '{premise.name}'",
                                   "quality")
        
        # Check intro quality
        intro_sentences = self._count_sentences(argument.intro)
        if intro_sentences < 2:
            result.add_issue(ValidationSeverity.INFO,
                           "Intro may be too brief (1 sentence)",
                           "quality")
        elif intro_sentences > 5:
            result.add_issue(ValidationSeverity.INFO,
                           "Intro may be too long",
                           "quality")
        
        # Check for inflammatory language (simple heuristic)
        inflammatory_words = [
            'obviously', 'clearly', 'undeniably', 'absolutely',
            'everyone knows', 'no one denies'
        ]
        
        all_text = (argument.intro + " " + argument.conclusion).lower()
        found_inflammatory = [word for word in inflammatory_words 
                             if word in all_text]
        
        if found_inflammatory:
            result.add_issue(ValidationSeverity.WARNING,
                           f"Potentially inflammatory language: {found_inflammatory}",
                           "quality")
    
    def _validate_logical_consistency(self, argument: Argument,
                                      result: ValidationResult) -> None:
        """Check for logical inconsistencies within each premise."""
        # Contradictions are only meaningful within the same premise.
        # Cross-premise polarity differences are normal and expected
        # (e.g. "exercise always helps" in premise 1 vs "rest is never
        # optional" in premise 2 should not flag a contradiction).
        contradictions = [
            ('always', 'never'),
            ('all', 'none'),
            ('every', 'no'),
            ('must', 'must not'),
            ('should', 'should not'),
        ]

        for premise in argument.premises:
            stmts = [s.text.lower() for s in premise.statements]
            for i, stmt1 in enumerate(stmts):
                for stmt2 in stmts[i + 1:]:
                    for word1, word2 in contradictions:
                        if word1 in stmt1 and word2 in stmt2:
                            result.add_issue(
                                ValidationSeverity.WARNING,
                                f"Potential contradiction within '{premise.name}'",
                                "logic",
                            )
                            break

        # Check if premises support the conclusion (basic keyword matching)
        conclusion_words = set(argument.conclusion.lower().split())
        support_count = 0
        for premise in argument.premises:
            for stmt in premise.statements:
                stmt_words = set(stmt.text.lower().split())
                if len(conclusion_words & stmt_words) >= 2:
                    support_count += 1

        if support_count == 0:
            result.add_issue(ValidationSeverity.WARNING,
                             "Premises may not support conclusion",
                             "logic")
    
    def _validate_sources(self, argument: Argument,
                         result: ValidationResult) -> None:
        """Validate sources if present."""
        all_sources = []
        for premise in argument.premises:
            all_sources.extend(premise.sources)
        
        if not all_sources:
            result.add_issue(ValidationSeverity.INFO,
                           "No sources provided",
                           "sources")
            return
        
        # Validate source format
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        invalid_urls = []
        for source in all_sources:
            if not url_pattern.match(source):
                invalid_urls.append(source[:50])
        
        if invalid_urls:
            result.add_issue(ValidationSeverity.WARNING,
                           f"Invalid URL format: {invalid_urls[:3]}",
                           "sources")
    
    def _count_sentences(self, text: str) -> int:
        """Count sentences in text."""
        # Simple sentence counting
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])
    
    def get_quality_label(self, score: float) -> str:
        """Get human-readable quality label from score."""
        if score >= self.QUALITY_EXCELLENT:
            return "Excellent ⭐"
        elif score >= self.QUALITY_GOOD:
            return "Good 👍"
        elif score >= self.QUALITY_FAIR:
            return "Fair 😐"
        else:
            return "Poor ❌"


    def _validate_five_ws(self, argument: Argument,
                          result: ValidationResult) -> None:
        """Check that each premise has Five-Ws content for interactive Q&A.

        Missing 5W fields mean the policy layer cannot answer user questions
        like "why is this true?" or "when does this apply?".  Reported as INFO
        (not WARNING) because manually authored arguments may intentionally omit
        some fields.
        """
        five_ws = ("what", "why", "how", "when", "where")

        for premise in argument.premises:
            missing = [w for w in five_ws if not getattr(premise, w)]
            if missing:
                result.add_issue(
                    ValidationSeverity.INFO,
                    f"Premise '{premise.name}' missing Five-Ws fields: {missing}",
                    "five_ws",
                )


def validate_argument(argument: Argument) -> ValidationResult:
    """Convenience function to validate an argument.
    
    Args:
        argument: Argument to validate.
        
    Returns:
        ValidationResult with pass/fail, score, and issues.
    """
    validator = ArgumentValidator()
    return validator.validate(argument)


def validate_directory(path: Path | str) -> list[tuple[str, ValidationResult]]:
    """Validate all arguments in a directory (recursively).
    
    Args:
        path: Directory containing argument subdirectories.
        
    Returns:
        List of (argument_name, ValidationResult) tuples.
    """
    from difficult_dialogs.arguments import Argument
    
    path = Path(path)
    results = []
    
    # Find all intro.dialog files recursively
    for intro_file in path.rglob("intro.dialog"):
        arg_dir = intro_file.parent
        
        try:
            arg = Argument().load(arg_dir)
            result = validate_argument(arg)
            results.append((arg.name, result))
        except Exception as e:
            results.append((
                arg_dir.name,
                ValidationResult(
                    passed=False,
                    score=0.0,
                    issues=[ValidationIssue(
                        ValidationSeverity.CRITICAL,
                        f"Failed to load: {e}",
                        "loading"
                    )]
                )
            ))
    
    return results
