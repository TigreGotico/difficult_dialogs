"""Unit tests for difficult_dialogs.arguments.Argument."""
import pytest
from pathlib import Path
from difficult_dialogs.arguments import Argument
from difficult_dialogs.exceptions import ArgumentLoadError, ArgumentSaveError
from difficult_dialogs.premises import Premise


EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
COGITO_DIR = EXAMPLES_DIR / "i_think_therefore_i_am"


def test_default_initialization() -> None:
    """Argument initializes with empty defaults."""
    arg = Argument()
    assert arg.name == ""
    assert arg.intro == ""
    assert arg.conclusion == ""
    assert arg.premises == []
    assert arg.is_true is True


def test_named_argument() -> None:
    """Argument can be created with name, intro, conclusion."""
    arg = Argument(
        name="Test Argument",
        intro="This is the intro",
        conclusion="This is the conclusion"
    )
    assert arg.name == "Test Argument"
    assert arg.intro == "This is the intro"
    assert arg.conclusion == "This is the conclusion"


def test_add_premise() -> None:
    """Add premise to argument."""
    arg = Argument()
    premise = Premise(name="test_premise")
    premise.add_statement("statement 1")
    
    result = arg.add_premise(premise)
    
    assert len(arg.premises) == 1
    assert arg.get_premise("test_premise") is premise
    assert result is arg  # chaining


def test_add_premise_requires_name() -> None:
    """Premise must have a name."""
    arg = Argument()
    premise = Premise(name="")
    
    with pytest.raises(ValueError):
        arg.add_premise(premise)


def test_get_premise_not_found() -> None:
    """Get non-existent premise returns None."""
    arg = Argument()
    assert arg.get_premise("nonexistent") is None


def test_load_from_directory() -> None:
    """Load argument from directory structure."""
    arg = Argument()
    arg.load(COGITO_DIR)

    assert arg.name == "i think therefore i am"


def test_from_directory_classmethod() -> None:
    """from_directory() is equivalent to Argument().load()."""
    arg = Argument.from_directory(COGITO_DIR)
    assert arg.name == "i think therefore i am"
    assert arg.intro != ""
    assert len(arg.premises) > 0
    assert arg.intro != ""
    assert arg.conclusion != ""
    assert len(arg.premises) > 0


def test_premise_names_property() -> None:
    """premise_names returns list of all premise name strings."""
    arg = Argument()
    arg.add_premise(Premise(name="alpha").add_statement("s1"))
    arg.add_premise(Premise(name="beta").add_statement("s2"))
    assert arg.premise_names == ["alpha", "beta"]



def test_load_nonexistent_directory() -> None:
    """Loading nonexistent directory raises ArgumentLoadError."""
    arg = Argument()
    with pytest.raises(ArgumentLoadError):
        arg.load("/nonexistent/path")


def test_load_file_instead_of_directory() -> None:
    """Loading a file path raises ArgumentLoadError."""
    arg = Argument()
    with pytest.raises(ArgumentLoadError):
        arg.load(__file__)


def test_is_true_when_all_premises_agreed() -> None:
    """Argument is true when all premises are agreed."""
    arg = Argument()
    
    p1 = Premise(name="p1")
    p1.add_statement("s1")
    arg.add_premise(p1)
    
    p2 = Premise(name="p2")
    p2.add_statement("s2")
    arg.add_premise(p2)
    
    assert arg.is_true is True
    
    p1.statements[0].disagree()
    assert arg.is_true is False


def test_is_complete() -> None:
    """Argument is complete when it has premises."""
    arg = Argument()
    assert arg.is_complete is False
    
    arg.add_premise(Premise(name="test"))
    assert arg.is_complete is True


def test_get_next_premise() -> None:
    """Get next unspoken premise."""
    arg = Argument()
    arg.add_premise(Premise(name="p1").add_statement("s1"))
    arg.add_premise(Premise(name="p2").add_statement("s2"))
    
    cache: set[str] = set()
    premise = arg.get_next_premise(cache)
    assert premise is not None
    assert premise.name in ("p1", "p2")
    
    cache.add(premise.name)
    next_premise = arg.get_next_premise(cache)
    assert next_premise is not None
    assert next_premise.name != premise.name


def test_to_dict() -> None:
    """Convert argument to dictionary."""
    arg = Argument(name="test", intro="intro text", conclusion="conclusion text")
    arg.add_premise(Premise(name="p1").add_statement("s1"))
    
    data = arg.to_dict()
    
    assert data["name"] == "test"
    assert data["intro"] == "intro text"
    assert data["conclusion"] == "conclusion text"
    assert len(data["premises"]) == 1
    assert data["is_true"] is True


def test_from_dict_roundtrip() -> None:
    """Create argument from dictionary roundtrip."""
    data = {
        "name": "roundtrip",
        "intro": "start here",
        "conclusion": "end here",
        "premises": [
            {
                "name": "p1",
                "description": "Premise 1",
                "statements": ["s1", "s2"],
                "support": ["supp1"],
                "sources": ["http://example.com"],
            }
        ],
    }
    
    arg = Argument.from_dict(data)
    
    assert arg.name == "roundtrip"
    assert arg.intro == "start here"
    assert arg.conclusion == "end here"
    assert len(arg.premises) == 1
    assert len(arg.premises[0].statements) == 2


class TestArgumentSave:
    """Tests for Argument.save() round-trip."""

    def test_save_creates_directory(self, tmp_path: Path) -> None:
        """save() creates the output directory."""
        arg = Argument(name="test", intro="Intro text.", conclusion="Conclusion text.")
        dest = arg.save(tmp_path / "my_arg")
        assert dest.is_dir()

    def test_save_writes_intro_and_conclusion(self, tmp_path: Path) -> None:
        """save() writes intro.dialog and conclusion.conclusion."""
        arg = Argument(name="test", intro="Hello.", conclusion="Goodbye.")
        dest = arg.save(tmp_path / "arg")
        assert (dest / "intro.dialog").read_text() == "Hello."
        assert (dest / "conclusion.conclusion").read_text() == "Goodbye."

    def test_save_writes_premise_files(self, tmp_path: Path) -> None:
        """save() writes all premise field files."""
        arg = Argument(name="test", intro="I.", conclusion="C.")
        p = Premise(name="premise_one")
        p.add_statement("Claim A.")
        p.add_statement("Claim B.")
        p.add_support("Support text.")
        p.add_source("https://example.com")
        p.add_what("What it means.")
        p.add_why("Why it is true.")
        p.add_how("How it works.")
        p.add_when("When it applies.")
        p.add_where("Where it is observed.")
        arg.add_premise(p)

        dest = arg.save(tmp_path / "arg")
        pdir = dest / "premise_one"
        assert pdir.is_dir()
        assert (pdir / "premise_one.premise").exists()
        assert (pdir / "premise_one.support").exists()
        assert (pdir / "premise_one.source").exists()
        assert (pdir / "premise_one.what").exists()
        assert (pdir / "premise_one.when").exists()
        assert (pdir / "premise_one.where").exists()

    def test_save_skips_empty_fields(self, tmp_path: Path) -> None:
        """save() does not create files for empty premise fields."""
        arg = Argument(name="test", intro="I.", conclusion="C.")
        p = Premise(name="bare")
        p.add_statement("Only statement.")
        arg.add_premise(p)

        dest = arg.save(tmp_path / "arg")
        pdir = dest / "bare"
        assert (pdir / "bare.premise").exists()
        assert not (pdir / "bare.support").exists()
        assert not (pdir / "bare.what").exists()

    def test_save_load_roundtrip(self, tmp_path: Path) -> None:
        """save() then load() produces an identical argument."""
        arg = Argument(name="roundtrip", intro="Start.", conclusion="End.")
        p = Premise(name="p1")
        p.add_statement("Statement one.")
        p.add_statement("Statement two.")
        p.add_what("What this means.")
        p.add_when("When this applies.")
        p.add_where("Where observed.")
        arg.add_premise(p)

        dest = arg.save(tmp_path / "roundtrip")
        arg2 = Argument().load(dest)

        assert arg2.intro == "Start."
        assert arg2.conclusion == "End."
        p2 = arg2.get_premise("p1")
        assert p2 is not None
        assert [str(s) for s in p2.statements] == ["Statement one.", "Statement two."]
        assert p2.what == ["What this means."]
        assert p2.when == ["When this applies."]
        assert p2.where == ["Where observed."]

    def test_save_without_path_raises_when_no_source_path(self) -> None:
        """save() with no path and no self.path raises ArgumentSaveError."""
        arg = Argument(name="test", intro="I.", conclusion="C.")
        with pytest.raises(ArgumentSaveError, match="No path specified"):
            arg.save()

    def test_save_updates_self_path(self, tmp_path: Path) -> None:
        """save() updates self.path so subsequent save() with no arg works."""
        arg = Argument(name="test", intro="I.", conclusion="C.")
        dest = arg.save(tmp_path / "arg")
        assert arg.path == dest
        # Second save with no argument should reuse the path
        arg.save()
        assert (dest / "intro.dialog").exists()



def test_str_is_name() -> None:
    """String representation is argument name."""
    arg = Argument(name="My Argument")
    assert str(arg) == "My Argument"


def test_bool_returns_is_true() -> None:
    """Boolean conversion returns is_true."""
    arg = Argument()
    arg.add_premise(Premise(name="p1").add_statement("s1"))
    
    assert bool(arg) is True
    
    arg.premises[0].statements[0].disagree()
    assert bool(arg) is False


# ---------------------------------------------------------------------------
# Argument.diff()
# ---------------------------------------------------------------------------

def _make_arg(name: str = "test", intro: str = "I.", conclusion: str = "C.",
              premises: list[tuple[str, list[str]]] | None = None) -> Argument:
    arg = Argument(name=name, intro=intro, conclusion=conclusion)
    for pname, stmts in (premises or []):
        p = Premise(name=pname)
        for s in stmts:
            p.add_statement(s)
        arg.add_premise(p)
    return arg


def test_diff_no_changes() -> None:
    """diff returns empty result when arguments are identical."""
    a = _make_arg(premises=[("p1", ["s1", "s2"])])
    b = _make_arg(premises=[("p1", ["s1", "s2"])])
    result = a.diff(b)
    assert result == {"meta": {}, "added_premises": [], "removed_premises": [], "modified_premises": {}}


def test_diff_meta_changes() -> None:
    """diff reports name/intro/conclusion changes."""
    a = _make_arg(name="old", intro="Old intro.", conclusion="Old end.")
    b = _make_arg(name="new", intro="New intro.", conclusion="New end.")
    result = a.diff(b)
    assert result["meta"]["name"] == ("old", "new")
    assert result["meta"]["intro"] == ("Old intro.", "New intro.")
    assert result["meta"]["conclusion"] == ("Old end.", "New end.")


def test_diff_added_premise() -> None:
    """diff detects premises in other that are absent in self."""
    a = _make_arg(premises=[("p1", ["s1"])])
    b = _make_arg(premises=[("p1", ["s1"]), ("p2", ["s2"])])
    result = a.diff(b)
    assert result["added_premises"] == ["p2"]
    assert result["removed_premises"] == []


def test_diff_removed_premise() -> None:
    """diff detects premises in self that are absent in other."""
    a = _make_arg(premises=[("p1", ["s1"]), ("p2", ["s2"])])
    b = _make_arg(premises=[("p1", ["s1"])])
    result = a.diff(b)
    assert result["removed_premises"] == ["p2"]
    assert result["added_premises"] == []


def test_diff_modified_premise_statements() -> None:
    """diff reports added/removed statements within a shared premise."""
    a = _make_arg(premises=[("p1", ["s1", "s2"])])
    b = _make_arg(premises=[("p1", ["s1", "s3"])])
    result = a.diff(b)
    mod = result["modified_premises"]["p1"]
    assert mod["added_statements"] == ["s3"]
    assert mod["removed_statements"] == ["s2"]


def test_diff_unchanged_premise_not_in_modified() -> None:
    """Premises with identical statements are not in modified_premises."""
    a = _make_arg(premises=[("p1", ["s1"]), ("p2", ["s2"])])
    b = _make_arg(premises=[("p1", ["s1"]), ("p2", ["s2", "s3"])])
    result = a.diff(b)
    assert "p1" not in result["modified_premises"]
    assert "p2" in result["modified_premises"]


# ---------------------------------------------------------------------------
# Argument.merge()
# ---------------------------------------------------------------------------

def test_merge_combines_premises() -> None:
    """Merged argument contains premises from all source arguments."""
    a = _make_arg(name="a", premises=[("p1", ["s1"])])
    b = _make_arg(name="b", premises=[("p2", ["s2"])])
    m = Argument.merge(a, b)
    assert {p.name for p in m.premises} == {"p1", "p2"}


def test_merge_inherits_meta_from_first() -> None:
    """Name, intro, conclusion default to the first argument's values."""
    a = _make_arg(name="first", premises=[("p1", ["s1"])])
    b = _make_arg(name="second", premises=[("p2", ["s2"])])
    m = Argument.merge(a, b)
    assert m.name == "first"


def test_merge_explicit_meta_overrides() -> None:
    """Explicit name/intro/conclusion override source defaults."""
    a = _make_arg(name="a", premises=[("p1", ["s1"])])
    b = _make_arg(name="b", premises=[("p2", ["s2"])])
    m = Argument.merge(a, b, name="merged", intro="Hello", conclusion="Bye")
    assert m.name == "merged"
    assert m.intro == "Hello"
    assert m.conclusion == "Bye"


def test_merge_keep_first_on_conflict() -> None:
    """keep_first: first premise wins on duplicate name."""
    a = _make_arg(premises=[("p1", ["original"])])
    b = _make_arg(premises=[("p1", ["replacement"])])
    m = Argument.merge(a, b, on_conflict="keep_first")
    assert m.get_premise("p1").statements[0].text == "original"


def test_merge_keep_last_on_conflict() -> None:
    """keep_last: last premise wins on duplicate name."""
    a = _make_arg(premises=[("p1", ["original"])])
    b = _make_arg(premises=[("p1", ["replacement"])])
    m = Argument.merge(a, b, on_conflict="keep_last")
    assert m.get_premise("p1").statements[0].text == "replacement"


def test_merge_error_on_conflict() -> None:
    """on_conflict='error' raises ValueError for duplicate premise names."""
    a = _make_arg(premises=[("p1", ["s1"])])
    b = _make_arg(premises=[("p1", ["s2"])])
    with pytest.raises(ValueError, match="Duplicate premise name"):
        Argument.merge(a, b, on_conflict="error")


def test_merge_requires_two_args() -> None:
    """merge() with fewer than two arguments raises ValueError."""
    a = _make_arg(premises=[("p1", ["s1"])])
    with pytest.raises(ValueError, match="at least two"):
        Argument.merge(a)


def test_merge_invalid_on_conflict() -> None:
    """Unknown on_conflict strategy raises ValueError."""
    a = _make_arg(premises=[("p1", ["s1"])])
    b = _make_arg(premises=[("p2", ["s2"])])
    with pytest.raises(ValueError, match="Unknown on_conflict"):
        Argument.merge(a, b, on_conflict="bogus")


def test_merge_three_arguments() -> None:
    """merge() works with more than two source arguments."""
    a = _make_arg(premises=[("p1", ["s1"])])
    b = _make_arg(premises=[("p2", ["s2"])])
    c = _make_arg(premises=[("p3", ["s3"])])
    m = Argument.merge(a, b, c)
    assert len(m.premises) == 3
