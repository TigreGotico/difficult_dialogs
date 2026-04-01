"""Fluent builder API for constructing Argument objects programmatically.

Provides a chainable interface for building structured arguments without
touching the file-based format.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from difficult_dialogs.arguments import Argument
from difficult_dialogs.premises import Premise

if TYPE_CHECKING:
    pass


class PremiseBuilder:
    """Fluent builder for a single Premise.

    Created via :meth:`ArgumentBuilder.premise` and returned to the parent
    via :meth:`done`.
    """

    def __init__(self, name: str, parent: "ArgumentBuilder") -> None:
        self._premise = Premise(name=name)
        self._parent = parent

    # ------------------------------------------------------------------ #
    # core fields
    # ------------------------------------------------------------------ #

    def description(self, text: str) -> "PremiseBuilder":
        """Set a custom human-readable description."""
        self._premise.description = text
        return self

    def statement(self, text: str) -> "PremiseBuilder":
        """Add a core statement (claim)."""
        self._premise.add_statement(text)
        return self

    def support(self, text: str) -> "PremiseBuilder":
        """Add a comeback used when the user disagrees."""
        self._premise.add_support(text)
        return self

    def source(self, url: str) -> "PremiseBuilder":
        """Add a citation or URL."""
        self._premise.add_source(url)
        return self

    # ------------------------------------------------------------------ #
    # Five Ws + How
    # ------------------------------------------------------------------ #

    def what(self, text: str) -> "PremiseBuilder":
        """Add an answer to 'what?'"""
        self._premise.add_what(text)
        return self

    def why(self, text: str) -> "PremiseBuilder":
        """Add an answer to 'why?'"""
        self._premise.add_why(text)
        return self

    def how(self, text: str) -> "PremiseBuilder":
        """Add an answer to 'how?'"""
        self._premise.add_how(text)
        return self

    def when(self, text: str) -> "PremiseBuilder":
        """Add an answer to 'when?'"""
        self._premise.add_when(text)
        return self

    def where(self, text: str) -> "PremiseBuilder":
        """Add an answer to 'where?'"""
        self._premise.add_where(text)
        return self

    def who(self, text: str) -> "PremiseBuilder":
        """Add an answer to 'who?'"""
        self._premise.add_who(text)
        return self

    # ------------------------------------------------------------------ #
    # branching
    # ------------------------------------------------------------------ #

    def choice(
        self,
        text: str,
        outcome: str = "agree",
        next_premise: str | None = None,
        label: str | None = None,
    ) -> "PremiseBuilder":
        """Add a multiple-choice option to this premise.

        Args:
            text: Human-readable option text.
            outcome: Semantic outcome — ``"agree"``, ``"disagree"``,
                ``"clarify"``, or ``"skip"``.
            next_premise: Optional name of the premise to jump to when
                this option is selected.
            label: Short label (``"A"``, ``"B"``…). Auto-assigned if omitted.

        Returns:
            Self for method chaining.
        """
        self._premise.add_choice(text=text, outcome=outcome, next_premise=next_premise, label=label)
        return self

    def on_agree(self, premise_name: str) -> "PremiseBuilder":
        """Set the premise to jump to when the user agrees.

        Args:
            premise_name: Name of the target premise.

        Returns:
            Self for method chaining.
        """
        self._premise.on_agree = premise_name
        return self

    def on_disagree(self, premise_name: str) -> "PremiseBuilder":
        """Set the premise to jump to when the user disagrees.

        Args:
            premise_name: Name of the target premise.

        Returns:
            Self for method chaining.
        """
        self._premise.on_disagree = premise_name
        return self

    # ------------------------------------------------------------------ #
    # navigation
    # ------------------------------------------------------------------ #

    def done(self) -> "ArgumentBuilder":
        """Finish configuring this premise and return to the ArgumentBuilder."""
        self._parent._add_premise(self._premise)
        return self._parent

    def build(self) -> Premise:
        """Return the finished Premise (also registers it with the parent)."""
        self._parent._add_premise(self._premise)
        return self._premise


class ArgumentBuilder:
    """Fluent builder for :class:`~difficult_dialogs.arguments.Argument`.

    Example::

        from difficult_dialogs.builder import ArgumentBuilder

        arg = (
            ArgumentBuilder("climate_change")
            .intro("Let's discuss climate change.")
            .conclusion("The evidence is clear.")
            .premise("human_causation")
                .statement("97 % of climate scientists agree.")
                .support("The IPCC report summarises thousands of studies.")
                .source("https://www.ipcc.ch/")
                .why("Because CO₂ traps heat in the atmosphere.")
                .done()
            .build()
        )
    """

    def __init__(self, name: str) -> None:
        self._argument = Argument(name=name)
        self._premises: list[Premise] = []

    # ------------------------------------------------------------------ #
    # argument-level fields
    # ------------------------------------------------------------------ #

    def intro(self, text: str) -> "ArgumentBuilder":
        """Set the opening statement."""
        self._argument.intro = text
        return self

    def conclusion(self, text: str) -> "ArgumentBuilder":
        """Set the closing statement."""
        self._argument.conclusion = text
        return self

    def entry_point(self, premise_name: str) -> "ArgumentBuilder":
        """Set the name of the first premise to present.

        Useful for non-linear arguments where the starting node is not the
        first one added via :meth:`premise`.

        Args:
            premise_name: Name of the entry-point premise.

        Returns:
            Self for method chaining.
        """
        self._argument.entry_point = premise_name
        return self

    # ------------------------------------------------------------------ #
    # premise sub-builder
    # ------------------------------------------------------------------ #

    def premise(self, name: str) -> PremiseBuilder:
        """Start configuring a new premise and return a :class:`PremiseBuilder`.

        Call :meth:`PremiseBuilder.done` to return here.
        """
        return PremiseBuilder(name=name, parent=self)

    def add_premise(self, p: Premise) -> "ArgumentBuilder":
        """Directly attach a pre-built :class:`Premise`."""
        self._add_premise(p)
        return self

    # ------------------------------------------------------------------ #
    # internal
    # ------------------------------------------------------------------ #

    def _add_premise(self, p: Premise) -> None:
        """Register a premise (avoids duplicates by name)."""
        names = {existing.name for existing in self._premises}
        if p.name not in names:
            self._premises.append(p)

    # ------------------------------------------------------------------ #
    # terminal
    # ------------------------------------------------------------------ #

    def build(self) -> Argument:
        """Construct and return the finished :class:`Argument`."""
        for p in self._premises:
            self._argument.add_premise(p)
        return self._argument
