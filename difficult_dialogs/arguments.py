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
    entry_point: str = ""
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

    def next_premise(self, current_name: str, outcome: str = "agree") -> str | None:
        """Return the name of the next premise to visit after *current_name*.

        Resolution order:

        1. If the current premise has an explicit ``on_agree`` / ``on_disagree``
           target (depending on *outcome*), use it.
        2. If the current premise has ``ChoiceOption`` entries that carry a
           ``next_premise`` name for the chosen outcome, use the first match.
        3. Fall back to the insertion-order successor (linear behaviour,
           preserving backwards compatibility with flat argument files).

        Args:
            current_name: Name of the premise just presented.
            outcome: Semantic outcome — ``"agree"``, ``"disagree"``,
                ``"clarify"``, or ``"skip"``.  Only ``"agree"`` and
                ``"disagree"`` are used for branch resolution; everything
                else follows linear order.

        Returns:
            Name of the next premise, or ``None`` if the argument is finished.
        """
        current = self._premises.get(current_name)
        if current is None:
            return None

        # 1. Explicit on_agree / on_disagree branch
        if outcome == "agree" and current.on_agree:
            return current.on_agree if current.on_agree in self._premises else None
        if outcome == "disagree" and current.on_disagree:
            return current.on_disagree if current.on_disagree in self._premises else None

        # 2. ChoiceOption.next_premise for this outcome
        for choice in current.choices:
            if choice.outcome == outcome and choice.next_premise:
                if choice.next_premise in self._premises:
                    return choice.next_premise

        # 3. Linear fallback — insertion-order successor
        names = list(self._premises.keys())
        try:
            idx = names.index(current_name)
        except ValueError:
            return None
        next_idx = idx + 1
        return names[next_idx] if next_idx < len(names) else None
    
    def to_graph(self) -> "GraphData":
        """Extract the directed graph structure of this argument.

        Returns:
            A :class:`~difficult_dialogs.graph.GraphData` instance with
            nodes (premises), edges (agree/disagree/choice/linear), and
            the optional entry point.
        """
        from difficult_dialogs.graph import build_graph
        return build_graph(self)

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

    @classmethod
    def from_directory(cls, path: str | Path) -> Argument:
        """Create a new Argument loaded from *path*.

        Equivalent to ``Argument().load(path)`` but more idiomatic.

        Args:
            path: Path to the argument directory.

        Returns:
            New Argument instance populated from *path*.

        Raises:
            ArgumentLoadError: If path doesn't exist or is not a directory.
        """
        return cls().load(path)

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
                (premise.who,        ".who"),
            ]

            for items, ext in _FIELDS:
                if not items:
                    continue
                lines = [str(item) for item in items]
                (pdir / f"{premise.name}{ext}").write_text("\n".join(lines))

            # Write choices file
            if premise.choices:
                choice_lines: list[str] = []
                for opt in premise.choices:
                    line = f"{opt.label}) {opt.text}"
                    if opt.next_premise:
                        line += f" -> {opt.next_premise}"
                    else:
                        # record non-default outcomes explicitly
                        from difficult_dialogs.choices import _POSITIONAL_OUTCOMES
                        default = _POSITIONAL_OUTCOMES.get(opt.label, "agree")
                        if opt.outcome != default:
                            line += f" [{opt.outcome}]"
                    choice_lines.append(line)
                (pdir / f"{premise.name}.choices").write_text("\n".join(choice_lines))

            if premise.on_agree:
                (pdir / f"{premise.name}.on_agree").write_text(premise.on_agree)
            if premise.on_disagree:
                (pdir / f"{premise.name}.on_disagree").write_text(premise.on_disagree)

        self.path = dest
        return dest

    def to_dict(self) -> dict[str, Any]:
        """Convert argument to dictionary representation.
        
        Returns:
            Dictionary with argument data.
        """
        d: dict[str, Any] = {
            "name": self.name,
            "intro": self.intro,
            "conclusion": self.conclusion,
            "premises": [p.to_dict() for p in self.premises],
            "is_true": self.is_true,
        }
        if self.entry_point:
            d["entry_point"] = self.entry_point
        return d
    
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
            entry_point=data.get("entry_point", ""),
        )

        for premise_data in data.get("premises", []):
            premise = Premise.from_dict(premise_data)
            arg.add_premise(premise)

        return arg
    
    def diff(self, other: Argument) -> dict[str, Any]:
        """Compare this argument with *other* and return a structured diff.

        Useful for reviewing LLM-generated updates before committing them.

        Args:
            other: The argument to compare against (typically the updated version).

        Returns:
            Dictionary with keys:
            - ``meta``: changes to name/intro/conclusion (field → (old, new)).
            - ``added_premises``: premise names present in *other* but not here.
            - ``removed_premises``: premise names present here but not in *other*.
            - ``modified_premises``: names present in both where statements differ
              (name → {added_statements, removed_statements}).
        """
        meta: dict[str, tuple[str, str]] = {}
        for field in ("name", "intro", "conclusion"):
            old_val = getattr(self, field)
            new_val = getattr(other, field)
            if old_val != new_val:
                meta[field] = (old_val, new_val)

        self_names = set(self.premise_names)
        other_names = set(other.premise_names)

        added_premises = sorted(other_names - self_names)
        removed_premises = sorted(self_names - other_names)

        modified_premises: dict[str, dict[str, list[str]]] = {}
        for name in self_names & other_names:
            old_stmts = {s.text for s in self._premises[name].statements}
            new_stmts = {s.text for s in other._premises[name].statements}
            if old_stmts != new_stmts:
                modified_premises[name] = {
                    "added_statements": sorted(new_stmts - old_stmts),
                    "removed_statements": sorted(old_stmts - new_stmts),
                }

        return {
            "meta": meta,
            "added_premises": added_premises,
            "removed_premises": removed_premises,
            "modified_premises": modified_premises,
        }

    @classmethod
    def merge(
        cls,
        *args: Argument,
        name: str = "",
        intro: str = "",
        conclusion: str = "",
        on_conflict: str = "keep_first",
    ) -> Argument:
        """Merge premises from multiple arguments into a new Argument.

        Premises with duplicate names are handled according to *on_conflict*:

        - ``"keep_first"`` — first occurrence wins (default).
        - ``"keep_last"``  — last occurrence wins.
        - ``"error"``      — raise ``ValueError`` on first duplicate name.

        The merged argument's *name*, *intro*, and *conclusion* may be
        provided explicitly; otherwise they fall back to the first argument's
        values.

        Args:
            *args: Two or more Argument instances to merge.
            name: Name for the merged argument (optional).
            intro: Intro text (optional, falls back to first arg).
            conclusion: Conclusion text (optional, falls back to first arg).
            on_conflict: Conflict resolution strategy.

        Returns:
            New Argument containing all (or winning) premises.

        Raises:
            ValueError: If fewer than two arguments are given, or
                        *on_conflict* is ``"error"`` and a duplicate is found.
        """
        if len(args) < 2:
            raise ValueError("merge() requires at least two arguments")
        if on_conflict not in ("keep_first", "keep_last", "error"):
            raise ValueError(f"Unknown on_conflict strategy: {on_conflict!r}")

        merged = cls(
            name=name or args[0].name,
            intro=intro or args[0].intro,
            conclusion=conclusion or args[0].conclusion,
        )

        for source in args:
            for premise in source.premises:
                if premise.name in merged._premises:
                    if on_conflict == "error":
                        raise ValueError(
                            f"Duplicate premise name {premise.name!r} "
                            f"found while merging arguments"
                        )
                    if on_conflict == "keep_first":
                        continue  # skip duplicate
                    # keep_last: fall through to overwrite
                merged._premises[premise.name] = premise

        return merged

    def __bool__(self) -> bool:
        """Return whether this argument is currently accepted as true."""
        return self.is_true
    
    def __str__(self) -> str:
        """Return the argument name."""
        return self.name
