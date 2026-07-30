"""Graph data model for argument visualization.

Extracts the directed graph structure from an :class:`~difficult_dialogs.arguments.Argument`
into a renderer-agnostic data model (:class:`GraphData`) that can be serialized
to Mermaid, DOT, JSON, or any other graph format.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from difficult_dialogs.arguments import Argument


@dataclass
class GraphNode:
    """A single premise in the argument graph."""

    name: str
    statement_count: int = 0
    has_choices: bool = False
    has_support: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "statement_count": self.statement_count,
            "has_choices": self.has_choices,
            "has_support": self.has_support,
        }


@dataclass
class GraphEdge:
    """A directed edge between two premises."""

    source: str
    target: str
    label: str  # "agree", "disagree", "choice:<label>", "next"
    is_linear_fallback: bool = False

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "label": self.label,
            "is_linear_fallback": self.is_linear_fallback,
        }


@dataclass
class GraphData:
    """Complete graph representation of an argument's premise structure."""

    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    entry_point: str | None = None

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "entry_point": self.entry_point,
        }


def build_graph(argument: Argument) -> GraphData:
    """Extract the directed graph from an argument.

    Builds nodes from premises and edges from ``on_agree``, ``on_disagree``,
    ``ChoiceOption.next_premise``, and linear insertion-order fallback.

    Args:
        argument: The argument to extract the graph from.

    Returns:
        A :class:`GraphData` instance.
    """
    all_names: list[str] = list(argument._premises.keys())
    all_names_set: set[str] = set(all_names)

    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    has_explicit_edges = False

    for name, premise in argument._premises.items():
        nodes.append(GraphNode(
            name=name,
            statement_count=len(premise.statements),
            has_choices=bool(premise.choices),
            has_support=bool(premise.support),
        ))

        # Explicit on_agree edge
        if premise.on_agree and premise.on_agree in all_names_set:
            edges.append(GraphEdge(
                source=name, target=premise.on_agree,
                label="agree", is_linear_fallback=False,
            ))
            has_explicit_edges = True

        # Explicit on_disagree edge
        if premise.on_disagree and premise.on_disagree in all_names_set:
            edges.append(GraphEdge(
                source=name, target=premise.on_disagree,
                label="disagree", is_linear_fallback=False,
            ))
            has_explicit_edges = True

        # Choice edges
        for choice in premise.choices:
            if choice.next_premise and choice.next_premise in all_names_set:
                edges.append(GraphEdge(
                    source=name, target=choice.next_premise,
                    label=f"choice:{choice.label}",
                    is_linear_fallback=False,
                ))
                has_explicit_edges = True

    # Linear fallback edges (insertion-order next)
    for i, name in enumerate(all_names):
        if i + 1 < len(all_names):
            # Check if this node already has an explicit outgoing edge
            has_outgoing = any(
                e.source == name and not e.is_linear_fallback for e in edges
            )
            # Always add the fallback edge — renderers filter via the flag
            if not has_outgoing:
                edges.append(GraphEdge(
                    source=name, target=all_names[i + 1],
                    label="next", is_linear_fallback=True,
                ))

    return GraphData(
        nodes=nodes,
        edges=edges,
        entry_point=argument.entry_point or None,
    )
