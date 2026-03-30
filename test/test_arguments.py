"""Unit tests for difficult_dialogs.arguments.Argument."""
import os
import pytest
from difficult_dialogs.arguments import Argument

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")
TEMPLATE_DIR = os.path.join(EXAMPLES_DIR, "argument_template")
COGITO_DIR = os.path.join(EXAMPLES_DIR, "i_think_therefore_i_am")


def test_load_from_directory() -> None:
    arg = Argument(path=TEMPLATE_DIR)
    assert arg.description  # non-empty
    assert len(arg.premises) > 0


def test_is_true_after_load() -> None:
    arg = Argument(path=TEMPLATE_DIR)
    assert arg.is_true is True
    assert bool(arg) is True


def test_intro_and_conclusion_set() -> None:
    arg = Argument(path=TEMPLATE_DIR)
    assert str(arg.intro_statement).strip() != ""
    assert str(arg.conclusion_statement).strip() != ""


def test_next_statement_returns_string() -> None:
    """next_statement() on a legacy-style Argument (examples/arguments.py API)
    is not the same object as Argument from the package — we test the package
    Argument API (choose_next_statement via policy) elsewhere.
    Here we verify loading and as_json."""
    arg = Argument(path=TEMPLATE_DIR)
    data = arg.as_json
    assert "premises" in data
    assert "intro" in data
    assert "conclusion" in data
    assert "is_true" in data


def test_cogito_argument_loads() -> None:
    arg = Argument(path=COGITO_DIR)
    assert len(arg.premises) == 3


def test_cogito_sources() -> None:
    arg = Argument(path=COGITO_DIR)
    assert len(arg.sources) > 0


def test_cogito_support() -> None:
    arg = Argument(path=COGITO_DIR)
    assert len(arg.support_statements) > 0


def test_add_premise_from_string() -> None:
    arg = Argument()
    arg.add_premise("my premise")
    assert len(arg.premises) == 1
    assert arg.premises[0].description.text == "my premise"


def test_add_support_to_premise() -> None:
    arg = Argument()
    arg.add_premise("p1")
    arg.add_support("this supports p1", "p1")
    assert len(arg.premises[0].support_statements) == 1


def test_add_source_to_premise() -> None:
    arg = Argument()
    arg.add_premise("p1")
    arg.add_source("https://example.com", "p1")
    assert "https://example.com" in arg.premises[0].sources


def test_str_is_description() -> None:
    arg = Argument(description="test arg")
    assert str(arg) == "test arg"
