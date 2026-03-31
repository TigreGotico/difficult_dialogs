"""Unit tests for difficult_dialogs.premises.Premise."""
from difficult_dialogs.premises import Premise


def test_default_true() -> None:
    """Premise is true by default with no statements."""
    p = Premise(name="test")
    assert p.is_true is True
    assert p.name == "test"


def test_description_from_name() -> None:
    """Description defaults from name if not provided."""
    p = Premise(name="my_premise")
    assert p.description == "My premise"


def test_custom_description() -> None:
    """Custom description is used when provided."""
    p = Premise(name="test", description="Custom description")
    assert p.description == "Custom description"


def test_truth_when_all_statements_true() -> None:
    """Premise is true when all statements are agreed."""
    p = Premise(name="claim")
    p.add_statement("fact one")
    p.add_statement("fact two")
    assert p.is_true is True
    assert bool(p) is True


def test_false_when_any_statement_false() -> None:
    """Premise is false when any statement is disagreed."""
    p = Premise(name="claim")
    p.add_statement("fact one")
    p.add_statement("fact two")
    p.statements[0].disagree()
    assert p.is_true is False
    assert bool(p) is False


def test_no_statements_is_true() -> None:
    """A premise with no statements has vacuous truth."""
    p = Premise(name="bare claim")
    assert p.is_true is True


def test_add_statement_from_string() -> None:
    """Add statement from string creates Statement object."""
    p = Premise(name="desc")
    p.add_statement("s1")
    assert len(p.statements) == 1
    assert p.statements[0].text == "s1"


def test_add_statement_chaining() -> None:
    """Add statement returns self for chaining."""
    p = Premise(name="desc")
    result = p.add_statement("s1").add_statement("s2")
    assert len(p.statements) == 2
    assert result is p


def test_add_support_statement() -> None:
    """Support statements can be added."""
    p = Premise(name="desc")
    p.add_support("support line")
    assert len(p.support) == 1
    assert "support line" in p.support


def test_add_source() -> None:
    """Sources can be added."""
    p = Premise(name="desc")
    p.add_source("https://example.com")
    assert "https://example.com" in p.sources


def test_add_what_why_how() -> None:
    """Five Ws explanations can be added."""
    p = Premise(name="desc")
    p.add_what("it is a thing")
    p.add_why("because reasons")
    p.add_how("by doing stuff")
    p.add_when("yesterday")
    p.add_where("everywhere")
    
    assert "it is a thing" in p.what
    assert "because reasons" in p.why
    assert "by doing stuff" in p.how
    assert "yesterday" in p.when
    assert "everywhere" in p.where


def test_get_next_statement() -> None:
    """Get next unspoken statement."""
    p = Premise(name="test")
    p.add_statement("first")
    p.add_statement("second")
    
    cache: set[str] = set()
    stmt = p.get_next_statement(cache)
    assert stmt is not None
    assert stmt.text in ("first", "second")
    
    cache.add(stmt.text)
    next_stmt = p.get_next_statement(cache)
    assert next_stmt is not None
    assert next_stmt.text not in cache
    
    cache.add(next_stmt.text)
    assert p.get_next_statement(cache) is None


def test_get_support() -> None:
    """Get unused support statement."""
    p = Premise(name="test")
    p.add_support("support 1")
    p.add_support("support 2")
    
    cache: set[str] = set()
    support = p.get_support(cache)
    assert support in ("support 1", "support 2")
    
    cache.add(support)
    next_support = p.get_support(cache)
    assert next_support is not None
    assert next_support not in cache
    
    cache.add(next_support)
    assert p.get_support(cache) is None


def test_to_dict() -> None:
    """Convert premise to dictionary."""
    p = Premise(name="test", description="Test premise")
    p.add_statement("stmt1")
    p.add_support("supp1")
    p.add_source("http://example.com")
    
    data = p.to_dict()
    assert data["name"] == "test"
    assert data["description"] == "Test premise"
    assert data["statements"] == ["stmt1"]
    assert data["support"] == ["supp1"]
    assert data["sources"] == ["http://example.com"]
    assert data["is_true"] is True


def test_from_dict_roundtrip() -> None:
    """Create premise from dictionary roundtrip."""
    data = {
        "name": "roundtrip",
        "description": "Test roundtrip",
        "statements": ["s1", "s2"],
        "support": ["supp1"],
        "sources": ["http://example.com"],
        "what": ["what explanation"],
        "why": ["why explanation"],
        "how": ["how explanation"],
        "when": ["when explanation"],
        "where": ["where explanation"],
    }

    p = Premise.from_dict(data)
    assert p.name == "roundtrip"
    assert len(p.statements) == 2
    assert len(p.support) == 1
    assert len(p.sources) == 1
    assert "what explanation" in p.what
    assert "why explanation" in p.why
    assert "how explanation" in p.how
    assert "when explanation" in p.when
    assert "where explanation" in p.where


def test_str_is_description() -> None:
    """String representation is description."""
    p = Premise(name="my claim", description="My claim description")
    assert str(p) == "My claim description"
