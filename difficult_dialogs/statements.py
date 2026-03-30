"""Statement module - the atomic unit of dialog.

A Statement is a text sentence that may be True or False based on user agreement.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Statement:
    """A statement that can be agreed or disagreed with.
    
    Attributes:
        text: The text content of this statement.
        agreed: Whether the user has agreed with this statement.
    """
    text: str
    agreed: bool = field(default=True, init=False)

    def agree(self) -> None:
        """Mark this statement as agreed (True)."""
        self.agreed = True
    
    def disagree(self) -> None:
        """Mark this statement as disagreed (False)."""
        self.agreed = False
    
    def __bool__(self) -> bool:
        """Return whether this statement is currently agreed."""
        return self.agreed
    
    def __str__(self) -> str:
        """Return the statement text."""
        return self.text
    
    def __eq__(self, other: object) -> bool:
        """Check equality based on text content."""
        if not isinstance(other, Statement):
            return NotImplemented
        return self.text == other.text
    
    def __hash__(self) -> int:
        """Hash based on text for use in sets/dicts."""
        return hash(self.text)
