"""Tests for difficult_dialogs.graph — graph data model extraction."""
from difficult_dialogs.builder import ArgumentBuilder
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
