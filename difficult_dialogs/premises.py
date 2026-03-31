"""Premise module - a collection of statements that form a logical unit.

A Premise is True if all its statements are True (agreed by user).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from difficult_dialogs.statements import Statement


@dataclass
class Premise:
    """A premise containing statements that must all be agreed upon.
    
    A premise represents a single claim or assertion in an argument.
    It is considered True only when all its statements are agreed with.
    
    Attributes:
        name: Identifier for this premise.
        description: Human-readable description of the premise.
        statements: List of statements that must be agreed with.
        support: Supporting arguments used when user disagrees.
        sources: Evidence URLs or citations backing this premise.
        what: Explanations answering "what" questions.
        why: Explanations answering "why" questions.
        how: Explanations answering "how" questions.
        when: Contextual information about timing.
        where: Contextual information about location.
    """
    name: str
    description: str = ""
    statements: list[Statement] = field(default_factory=list)
    support: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    what: list[str] = field(default_factory=list)
    why: list[str] = field(default_factory=list)
    how: list[str] = field(default_factory=list)
    when: list[str] = field(default_factory=list)
    where: list[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Set description from name if not provided."""
        if not self.description:
            self.description = self.name.replace("_", " ").capitalize()
    
    @property
    def is_true(self) -> bool:
        """Return True if all statements are agreed."""
        return all(stmt.agreed for stmt in self.statements) if self.statements else True
    
    @property
    def is_complete(self) -> bool:
        """Return True if premise has at least one statement."""
        return len(self.statements) > 0
    
    def add_statement(self, text: str) -> Premise:
        """Add a statement to this premise.
        
        Args:
            text: The statement text.
            
        Returns:
            Self for method chaining.
        """
        self.statements.append(Statement(text))
        return self
    
    def add_support(self, text: str) -> Premise:
        """Add a support statement.
        
        Args:
            text: Support statement text.
            
        Returns:
            Self for method chaining.
        """
        if text not in self.support:
            self.support.append(text)
        return self
    
    def add_source(self, url: str) -> Premise:
        """Add a source URL or citation.
        
        Args:
            url: Source URL or citation text.
            
        Returns:
            Self for method chaining.
        """
        if url not in self.sources:
            self.sources.append(url)
        return self
    
    def add_what(self, text: str) -> Premise:
        """Add explanation for "what" questions."""
        if text not in self.what:
            self.what.append(text)
        return self
    
    def add_why(self, text: str) -> Premise:
        """Add explanation for "why" questions."""
        if text not in self.why:
            self.why.append(text)
        return self
    
    def add_how(self, text: str) -> Premise:
        """Add explanation for "how" questions."""
        if text not in self.how:
            self.how.append(text)
        return self
    
    def add_when(self, text: str) -> Premise:
        """Add contextual information about timing."""
        if text not in self.when:
            self.when.append(text)
        return self
    
    def add_where(self, text: str) -> Premise:
        """Add contextual information about location."""
        if text not in self.where:
            self.where.append(text)
        return self
    
    def get_next_statement(self, cache: set[str]) -> Statement | None:
        """Get the next unspoken statement.
        
        Args:
            cache: Set of already spoken statement texts.
            
        Returns:
            Next statement to present, or None if all spoken.
        """
        for stmt in self.statements:
            if stmt.text not in cache:
                return stmt
        return None
    
    def get_support(self, cache: set[str]) -> str | None:
        """Get an unused support statement.
        
        Args:
            cache: Set of already spoken texts.
            
        Returns:
            A support statement, or None if exhausted.
        """
        for text in self.support:
            if text not in cache:
                return text
        return None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "statements": [s.text for s in self.statements],
            "support": self.support.copy(),
            "sources": self.sources.copy(),
            "what": self.what.copy(),
            "why": self.why.copy(),
            "how": self.how.copy(),
            "when": self.when.copy(),
            "where": self.where.copy(),
            "is_true": self.is_true,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Premise:
        """Create a Premise from a dictionary.
        
        Args:
            data: Dictionary with premise data.
            
        Returns:
            New Premise instance.
        """
        premise = cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
        )
        
        for stmt_text in data.get("statements", []):
            premise.add_statement(stmt_text)
        
        for text in data.get("support", []):
            premise.add_support(text)
        
        for url in data.get("sources", []):
            premise.add_source(url)
        
        for text in data.get("what", []):
            premise.add_what(text)
        
        for text in data.get("why", []):
            premise.add_why(text)
        
        for text in data.get("how", []):
            premise.add_how(text)
        
        for text in data.get("when", []):
            premise.add_when(text)
        
        for text in data.get("where", []):
            premise.add_where(text)
        
        return premise
    
    def __bool__(self) -> bool:
        """Return whether this premise is currently accepted as true."""
        return self.is_true
    
    def __str__(self) -> str:
        """Return the premise description."""
        return self.description
