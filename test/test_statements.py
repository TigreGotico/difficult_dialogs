"""Unit tests for difficult_dialogs.statements.Statement."""
from difficult_dialogs.statements import Statement


def test_default_true() -> None:
    """Statements are true by default."""
    s = Statement("hello world")
    assert s.text == "hello world"
    assert s.agreed is True
    assert bool(s) is True


def test_str() -> None:
    """String representation returns text."""
    s = Statement("test text")
    assert str(s) == "test text"


def test_disagree_sets_false() -> None:
    """Disagree marks statement as False."""
    s = Statement("claim")
    s.disagree()
    assert s.agreed is False
    assert bool(s) is False


def test_agree_restores_true() -> None:
    """Agree marks statement as True."""
    s = Statement("claim")
    s.disagree()
    s.agree()
    assert s.agreed is True


def test_bool_returns_agreed() -> None:
    """Boolean conversion returns agreed state."""
    s = Statement("test")
    assert bool(s) is True
    s.disagree()
    assert bool(s) is False


def test_equality_by_text() -> None:
    """Equality based on text content."""
    s1 = Statement("same text")
    s2 = Statement("same text")
    s3 = Statement("different text")
    
    assert s1 == s2
    assert s1 != s3


def test_hash_for_dict_keys() -> None:
    """Hash based on text for use in sets/dicts."""
    s = Statement("test")
    stmt_set = {s, Statement("other")}
    assert s in stmt_set
    assert Statement("test") in stmt_set


def test_non_statement_equality() -> None:
    """Equality with non-Statement returns NotImplemented."""
    s = Statement("test")
    assert (s == "test") is False
    assert (s == 123) is False
