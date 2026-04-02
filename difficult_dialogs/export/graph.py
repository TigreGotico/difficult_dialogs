"""Graph export renderers — Mermaid, DOT (Graphviz), and JSON.

Each renderer takes a :class:`~difficult_dialogs.graph.GraphData` instance
and returns a string (or dict for JSON).
"""
from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from difficult_dialogs.graph import GraphData


def _sanitize_id(name: str) -> str:
    """Sanitize a premise name into a valid Mermaid/DOT node ID."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", name)


def _has_explicit_edges(graph: GraphData) -> bool:
    """Return True if the graph has any non-fallback edges."""
    return any(not e.is_linear_fallback for e in graph.edges)


def _visible_edges(graph: GraphData) -> list:
    """Return edges that should be rendered.

    For branching arguments, omit linear fallback edges.
    For purely linear arguments, show all edges.
    """
    if _has_explicit_edges(graph):
        return [e for e in graph.edges if not e.is_linear_fallback]
    return list(graph.edges)


def to_mermaid(graph: GraphData) -> str:
    """Render a graph as a Mermaid flowchart.

    Args:
        graph: Graph data to render.

    Returns:
        A Mermaid ``graph TD`` string renderable in GitHub, GitLab,
        Obsidian, and most modern Markdown tools.
    """
    lines = ["graph TD"]

    # Define nodes
    for node in graph.nodes:
        nid = _sanitize_id(node.name)
        label = node.name
        stmts = f"{node.statement_count} stmt" + ("s" if node.statement_count != 1 else "")
        display = f"{label}\\n({stmts})"

        if graph.entry_point and node.name == graph.entry_point:
            # Double brackets for entry point (stadium shape)
            lines.append(f'    {nid}(["{display}"])')
        elif node.has_choices:
            # Diamond for choice nodes
            lines.append(f'    {nid}{{"{display}"}}')
        else:
            lines.append(f'    {nid}["{display}"]')

    # Define edges
    for edge in _visible_edges(graph):
        src = _sanitize_id(edge.source)
        tgt = _sanitize_id(edge.target)
        if edge.label == "next":
            lines.append(f"    {src} --> {tgt}")
        else:
            lines.append(f'    {src} -->|"{edge.label}"| {tgt}')

    # Style entry point
    if graph.entry_point:
        eid = _sanitize_id(graph.entry_point)
        lines.append(f"    style {eid} stroke-width:3px")

    return "\n".join(lines) + "\n"


def to_dot(graph: GraphData) -> str:
    """Render a graph as a Graphviz DOT string.

    Args:
        graph: Graph data to render.

    Returns:
        A valid DOT ``digraph`` string.
    """
    lines = ["digraph {"]
    lines.append('    rankdir=TD;')
    lines.append('    node [shape=box, style=rounded];')

    # Nodes
    for node in graph.nodes:
        nid = _sanitize_id(node.name)
        label = node.name.replace('"', '\\"')
        stmts = f"{node.statement_count} stmt" + ("s" if node.statement_count != 1 else "")
        attrs = [f'label="{label}\\n({stmts})"']

        if graph.entry_point and node.name == graph.entry_point:
            attrs.append("penwidth=3")
        if node.has_choices:
            attrs.append("shape=diamond")

        lines.append(f'    {nid} [{", ".join(attrs)}];')

    # Edges
    for edge in _visible_edges(graph):
        src = _sanitize_id(edge.source)
        tgt = _sanitize_id(edge.target)
        label = edge.label.replace('"', '\\"')
        if edge.label == "next":
            lines.append(f"    {src} -> {tgt};")
        else:
            lines.append(f'    {src} -> {tgt} [label="{label}"];')

    lines.append("}")
    return "\n".join(lines) + "\n"


def to_graph_json(graph: GraphData) -> dict:
    """Render a graph as a JSON-serializable dict.

    Output structure::

        {
            "nodes": [{"name": ..., "statement_count": ..., "is_entry": bool, ...}],
            "edges": [{"source": ..., "target": ..., "label": ..., ...}],
            "entry_point": str | null
        }

    Args:
        graph: Graph data to render.

    Returns:
        A dict suitable for ``json.dumps()``.
    """
    nodes = []
    for node in graph.nodes:
        d = node.to_dict()
        d["is_entry"] = graph.entry_point is not None and node.name == graph.entry_point
        nodes.append(d)

    edges = [e.to_dict() for e in _visible_edges(graph)]

    return {
        "nodes": nodes,
        "edges": edges,
        "entry_point": graph.entry_point,
    }
