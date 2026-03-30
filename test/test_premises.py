"""Unit tests for difficult_dialogs.premises.Premise."""
import pytest
from difficult_dialogs.premises import Premise
from difficult_dialogs.statements import Statement
from difficult_dialogs.exceptions import UnrecognizedStatementFormat


def test_truth_when_all_statements_true() -> None:
    p = Premise("claim")
    p.add_statement("fact one")
    p.add_statement("fact two")
    assert p.is_true is True
    assert bool(p) is True


def test_false_when_any_statement_false() -> None:
    p = Premise("claim")
    p.add_statement("fact one")
    p.add_statement("fact two")
    p.statements[0].disagree()
    assert p.is_true is False
    assert bool(p) is False


def test_no_statements_is_true() -> None:
    """A premise with no statements has vacuous truth."""
    p = Premise("bare claim")
    assert p.is_true is True


def test_add_statement_from_string() -> None:
    p = Premise("desc")
    p.add_statement("s1")
    assert len(p.statements) == 1
    assert p.statements[0].text == "s1"


def test_add_statement_from_statement_object() -> None:
    p = Premise("desc")
    s = Statement("s1")
    p.add_statement(s)
    assert p.statements[0] is s


def test_add_statement_invalid_raises() -> None:
    p = Premise("desc")
    with pytest.raises(UnrecognizedStatementFormat):
        p.add_statement(123)  # type: ignore[arg-type]


def test_add_support_statement() -> None:
    p = Premise("desc")
    p.add_support_statement("support line")
    assert len(p.support_statements) == 1


def test_add_source() -> None:
    p = Premise("desc")
    p.add_source("https://example.com")
    assert "https://example.com" in p.sources


def test_agree_sets_all_true() -> None:
    p = Premise("claim")
    p.add_statement("s1")
    p.add_statement("s2")
    p.statements[0].disagree()
    assert p.is_true is False
    p.agree()
    assert p.is_true is True


def test_str_is_description() -> None:
    p = Premise("my claim")
    assert str(p) == "my claim"
