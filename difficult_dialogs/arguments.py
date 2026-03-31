"""Argument module - a collection of premises forming a complete argument.

An Argument is loaded from a folder structure with plain text files:

    my_argument/
    ├── intro.dialog              # Opening statement
    ├── conclusion.conclusion     # Final statement
    ├── premise_name/
    │   ├── premise_name.premise  # Supporting statements (one per line)
    │   ├── premise_name.support  # Fallback arguments when user disagrees
    │   ├── premise_name.source   # Evidence URLs
    │   ├── premise_name.what     # What it means
    │   ├── premise_name.why      # Why it is true
    │   ├── premise_name.how      # How it works
    │   ├── premise_name.when     # When it applies
    │   └── premise_name.where    # Where it is observed
    └── another_premise/
        └── ...
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from difficult_dialogs.exceptions import ArgumentLoadError, ArgumentSaveError
from difficult_dialogs.premises import Premise


@dataclass
class Argument:
    """An argument composed of multiple premises.
    
    An argument represents a complete dialog flow. It is considered True
    when all its premises have been successfully presented and agreed with.
    
    Attributes:
        name: Identifier for this argument.
        intro: Opening statement text.
        conclusion: Closing statement text.
        path: Optional path to load argument from.
    """
    name: str = ""
    intro: str = ""
    conclusion: str = ""
    path: Path | None = field(default=None, init=False)
    _premises: dict[str, Premise] = field(default_factory=dict, repr=False)
    
    @property
    def premises(self) -> list[Premise]:
        """Return list of all premises in this argument."""
        return list(self._premises.values())
    
    @property
    def premise_names(self) -> list[str]:
        """Return list of premise names."""
        return list(self._premises.keys())
    
    @property
    def is_true(self) -> bool:
        """Return True if all premises are agreed with."""
        return all(p.is_true for p in self.premises) if self.premises else True
    
    @property
    def is_complete(self) -> bool:
        """Return True if argument has at least one premise."""
        return len(self.premises) > 0
    
    def add_premise(self, premise: Premise) -> Argument:
        """Add a premise to this argument.
        
        Args:
            premise: The premise to add.
            
        Returns:
            Self for method chaining.
            
        Raises:
            ValueError: If premise name is empty.
        """
        if not premise.name:
            raise ValueError("Premise must have a name")
        
        self._premises[premise.name] = premise
        return self
    
    def get_premise(self, name: str) -> Premise | None:
        """Get a premise by name.
        
        Args:
            name: The premise name.
            
        Returns:
            The premise, or None if not found.
        """
        return self._premises.get(name)
    
    def get_next_premise(self, cache: set[str]) -> Premise | None:
        """Get the next unspoken premise.
        
        Args:
            cache: Set of already spoken premise names.
            
        Returns:
            Next premise to present, or None if all spoken.
        """
        for name, premise in self._premises.items():
            if name not in cache and premise.is_complete:
                return premise
        return None
    
    def load(self, path: str | Path) -> Argument:
        """Load argument from a directory structure.

        Expected layout::

            path/
            ├── intro.dialog
            ├── conclusion.conclusion
            └── premise_name/
                ├── premise_name.premise
                ├── premise_name.support   (optional)
                ├── premise_name.source    (optional)
                ├── premise_name.what      (optional)
                ├── premise_name.why       (optional)
                ├── premise_name.how       (optional)
                ├── premise_name.when      (optional)
                └── premise_name.where     (optional)

        Args:
            path: Path to the argument directory.

        Returns:
            Self for method chaining.

        Raises:
            ArgumentLoadError: If path doesn't exist or is not a directory.
        """
        path = Path(path)

        if not path.exists():
            raise ArgumentLoadError(f"Argument path does not exist: {path}")

        if not path.is_dir():
            raise ArgumentLoadError(f"Argument path must be a directory: {path}")

        self.path = path

        if not self.name:
            self.name = path.name.replace("_", " ")

        intro_file = path / "intro.dialog"
        if intro_file.exists():
            self.intro = intro_file.read_text().strip()

        conclusion_file = path / "conclusion.conclusion"
        if conclusion_file.exists():
            self.conclusion = conclusion_file.read_text().strip()

        for item in path.iterdir():
            if item.is_dir():
                self._load_premise(item)

        return self
    
    def _load_premise(self, premise_dir: Path) -> None:
        """Load a single premise from a subdirectory.

        Args:
            premise_dir: Directory containing premise files.
        """
        premise = Premise(name=premise_dir.name)

        for file in premise_dir.iterdir():
            if file.is_file():
                premise.apply_file(file)

        if premise.is_complete:
            self.add_premise(premise)
    
    def save(self, path: str | Path | None = None) -> Path:
        """Write the argument to the plain-text directory format.

        Creates one subdirectory per premise under *path*, writing each
        populated field to its corresponding file extension.  Empty lists
        are skipped so the directory stays clean.

        Args:
            path: Directory to write into.  If ``None``, re-uses
                  ``self.path`` (i.e. overwrites the directory it was
                  loaded from).  The directory is created if it does not
                  exist.

        Returns:
            The resolved ``Path`` that was written.

        Raises:
            ValueError: If no path is available (never loaded and none given).
        """
        dest = Path(path) if path is not None else self.path
        if dest is None:
            raise ArgumentSaveError(
                "No path specified and argument was not loaded from disk. "
                "Pass an explicit path to save()."
            )

        dest.mkdir(parents=True, exist_ok=True)

        if self.intro:
            (dest / "intro.dialog").write_text(self.intro)

        if self.conclusion:
            (dest / "conclusion.conclusion").write_text(self.conclusion)

        for premise in self.premises:
            pdir = dest / premise.name
            pdir.mkdir(exist_ok=True)

            _FIELDS: list[tuple[list[str], str]] = [
                (premise.statements, ".premise"),   # Statement objects → text
                (premise.support,    ".support"),
                (premise.sources,    ".source"),
                (premise.what,       ".what"),
                (premise.why,        ".why"),
                (premise.how,        ".how"),
                (premise.when,       ".when"),
                (premise.where,      ".where"),
            ]

            for items, ext in _FIELDS:
                if not items:
                    continue
                lines = [str(item) for item in items]
                (pdir / f"{premise.name}{ext}").write_text("\n".join(lines))

        self.path = dest
        return dest

    def to_dict(self) -> dict[str, Any]:
        """Convert argument to dictionary representation.
        
        Returns:
            Dictionary with argument data.
        """
        return {
            "name": self.name,
            "intro": self.intro,
            "conclusion": self.conclusion,
            "premises": [p.to_dict() for p in self.premises],
            "is_true": self.is_true,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Argument:
        """Create an Argument from a dictionary.
        
        Args:
            data: Dictionary with argument data.
            
        Returns:
            New Argument instance.
        """
        arg = cls(
            name=data.get("name", ""),
            intro=data.get("intro", ""),
            conclusion=data.get("conclusion", ""),
        )
        
        for premise_data in data.get("premises", []):
            premise = Premise.from_dict(premise_data)
            arg.add_premise(premise)
        
        return arg
    
    def __bool__(self) -> bool:
        """Return whether this argument is currently accepted as true."""
        return self.is_true
    
    def __str__(self) -> str:
        """Return the argument name."""
        return self.name
