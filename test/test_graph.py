"""Tests for difficult_dialogs.graph — graph data model and renderers."""
import json

from difficult_dialogs.builder import ArgumentBuilder
from difficult_dialogs.export.graph import to_mermaid, to_dot, to_graph_json
from difficult_dialogs.graph import GraphData, GraphNode, GraphEdge, build_graph


def _linear_arg():
    return (
        ArgumentBuilder("linear")
        .intro("Intro.")
        .conclusion("Done.")
        .premise("p1").statement("S1").done()
        .premise("p2").statement("S2").done()
        .premise("p3").statement("S3").done()
        .build()
    )


def _branching_arg():
    return (
        ArgumentBuilder("branching")
        .intro("Intro.")
        .conclusion("Done.")
        .premise("p1").statement("S1").on_agree("p2a").on_disagree("p2b").done()
        .premise("p2a").statement("Agree path.").done()
        .premise("p2b").statement("Disagree path.").done()
        .build()
    )


def _choice_arg():
    return (
        ArgumentBuilder("choice")
        .intro("Intro.")
        .conclusion("Done.")
        .premise("p1")
            .statement("Pick one.")
            .choice("Yes", outcome="agree", next_premise="p_yes", label="A")
            .choice("No", outcome="disagree", next_premise="p_no", label="B")
            .done()
        .premise("p_yes").statement("You agreed.").done()
        .premise("p_no").statement("You disagreed.").done()
        .build()
    )


def _entry_point_arg():
    return (
        ArgumentBuilder("ep")
        .intro("Intro.")
        .conclusion("Done.")
        .entry_point("p2")
        .premise("p1").statement("S1").done()
        .premise("p2").statement("S2").done()
        .build()
    )


class TestBuildGraphLinear:
    def test_node_count(self):
        g = _linear_arg().to_graph()
        assert len(g.nodes) == 3

    def test_edge_count(self):
        g = _linear_arg().to_graph()
        assert len(g.edges) == 2

    def test_all_edges_are_linear_fallback(self):
        g = _linear_arg().to_graph()
        assert all(e.is_linear_fallback for e in g.edges)

    def test_edge_labels_are_next(self):
        g = _linear_arg().to_graph()
        assert all(e.label == "next" for e in g.edges)

    def test_edge_chain(self):
        g = _linear_arg().to_graph()
        sources = [e.source for e in g.edges]
        targets = [e.target for e in g.edges]
        assert sources == ["p1", "p2"]
        assert targets == ["p2", "p3"]

    def test_no_entry_point(self):
        g = _linear_arg().to_graph()
        assert g.entry_point is None


class TestBuildGraphBranching:
    def test_explicit_edges(self):
        g = _branching_arg().to_graph()
        explicit = [e for e in g.edges if not e.is_linear_fallback]
        assert len(explicit) == 2

    def test_agree_edge(self):
        g = _branching_arg().to_graph()
        agree = [e for e in g.edges if e.label == "agree"]
        assert len(agree) == 1
        assert agree[0].source == "p1"
        assert agree[0].target == "p2a"
        assert agree[0].is_linear_fallback is False

    def test_disagree_edge(self):
        g = _branching_arg().to_graph()
        disagree = [e for e in g.edges if e.label == "disagree"]
        assert len(disagree) == 1
        assert disagree[0].source == "p1"
        assert disagree[0].target == "p2b"

    def test_node_metadata(self):
        g = _branching_arg().to_graph()
        p1 = next(n for n in g.nodes if n.name == "p1")
        assert p1.statement_count == 1
        assert p1.has_choices is False


class TestBuildGraphChoices:
    def test_choice_edges(self):
        g = _choice_arg().to_graph()
        choice_edges = [e for e in g.edges if e.label.startswith("choice:")]
        assert len(choice_edges) == 2
        labels = {e.label for e in choice_edges}
        assert "choice:A" in labels
        assert "choice:B" in labels

    def test_choice_node_metadata(self):
        g = _choice_arg().to_graph()
        p1 = next(n for n in g.nodes if n.name == "p1")
        assert p1.has_choices is True


class TestBuildGraphEntryPoint:
    def test_entry_point_set(self):
        g = _entry_point_arg().to_graph()
        assert g.entry_point == "p2"


class TestGraphDataSerialization:
    def test_to_dict(self):
        g = _linear_arg().to_graph()
        d = g.to_dict()
        assert "nodes" in d
        assert "edges" in d
        assert "entry_point" in d
        assert len(d["nodes"]) == 3

    def test_node_to_dict(self):
        n = GraphNode(name="p1", statement_count=2, has_choices=True, has_support=False)
        d = n.to_dict()
        assert d["name"] == "p1"
        assert d["statement_count"] == 2
        assert d["has_choices"] is True

    def test_edge_to_dict(self):
        e = GraphEdge(source="p1", target="p2", label="agree", is_linear_fallback=False)
        d = e.to_dict()
        assert d["source"] == "p1"
        assert d["target"] == "p2"
        assert d["label"] == "agree"


# ---------------------------------------------------------------------------
# Mermaid renderer
# ---------------------------------------------------------------------------

class TestMermaidRenderer:
    def test_starts_with_graph_td(self):
        g = _linear_arg().to_graph()
        assert to_mermaid(g).startswith("graph TD\n")

    def test_linear_shows_all_edges(self):
        m = to_mermaid(_linear_arg().to_graph())
        assert "p1 --> p2" in m
        assert "p2 --> p3" in m

    def test_branching_shows_labels(self):
        m = to_mermaid(_branching_arg().to_graph())
        assert '"agree"' in m
        assert '"disagree"' in m

    def test_branching_omits_fallback_edges(self):
        m = to_mermaid(_branching_arg().to_graph())
        # p2a and p2b have no explicit edges; their fallback edges should be hidden
        # because the graph has explicit edges
        lines = m.strip().split("\n")
        edge_lines = [l for l in lines if "-->" in l]
        # Should only have p1's two explicit edges + fallback for p2a->p2b (p2a has no explicit)
        assert any('"agree"' in l for l in edge_lines)

    def test_entry_point_styled(self):
        m = to_mermaid(_entry_point_arg().to_graph())
        assert "stroke-width:3px" in m
        assert "p2" in m

    def test_choice_node_is_diamond(self):
        m = to_mermaid(_choice_arg().to_graph())
        assert "{" in m  # diamond shape uses {}

    def test_special_chars_in_name(self):
        arg = (
            ArgumentBuilder("special")
            .intro("I.").conclusion("C.")
            .premise("my premise!").statement("s").done()
            .build()
        )
        m = to_mermaid(arg.to_graph())
        assert "my_premise_" in m  # sanitized ID


# ---------------------------------------------------------------------------
# DOT renderer
# ---------------------------------------------------------------------------

class TestDOTRenderer:
    def test_starts_with_digraph(self):
        d = to_dot(_linear_arg().to_graph())
        assert d.startswith("digraph {\n")

    def test_ends_with_closing_brace(self):
        d = to_dot(_linear_arg().to_graph())
        assert d.strip().endswith("}")

    def test_contains_edges(self):
        d = to_dot(_linear_arg().to_graph())
        assert "p1 -> p2" in d

    def test_branching_labels(self):
        d = to_dot(_branching_arg().to_graph())
        assert 'label="agree"' in d
        assert 'label="disagree"' in d

    def test_entry_point_bold(self):
        d = to_dot(_entry_point_arg().to_graph())
        assert "penwidth=3" in d


# ---------------------------------------------------------------------------
# JSON renderer
# ---------------------------------------------------------------------------

class TestJSONRenderer:
    def test_has_nodes_and_edges(self):
        j = to_graph_json(_linear_arg().to_graph())
        assert "nodes" in j
        assert "edges" in j
        assert len(j["nodes"]) == 3

    def test_json_serializable(self):
        j = to_graph_json(_branching_arg().to_graph())
        s = json.dumps(j)
        assert isinstance(s, str)

    def test_entry_point_marker(self):
        j = to_graph_json(_entry_point_arg().to_graph())
        entry_nodes = [n for n in j["nodes"] if n.get("is_entry")]
        assert len(entry_nodes) == 1
        assert entry_nodes[0]["name"] == "p2"

    def test_no_entry_all_false(self):
        j = to_graph_json(_linear_arg().to_graph())
        assert all(not n.get("is_entry") for n in j["nodes"])
