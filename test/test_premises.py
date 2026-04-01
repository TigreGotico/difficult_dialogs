"""Unit tests for difficult_dialogs.premises.Premise."""
import pytest
from pathlib import Path
from difficult_dialogs.arguments import Argument
from difficult_dialogs.premises import Premise


@pytest.fixture
def sample_arg() -> Argument:
    arg = Argument(name="test", intro="I.", conclusion="C.")
    p = Premise(name="p1")
    p.add_statement("s1")
    arg.add_premise(p)
    return arg


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


def test_apply_file_premise_extension(tmp_path) -> None:
    """apply_file() loads statements from a .premise file."""
    from pathlib import Path
    f = tmp_path / "p.premise"
    f.write_text("Claim one.\nClaim two.\n")
    p = Premise(name="p")
    p.apply_file(f)
    assert [str(s) for s in p.statements] == ["Claim one.", "Claim two."]


def test_apply_file_five_ws(tmp_path) -> None:
    """apply_file() loads all Five-Ws extensions."""
    from pathlib import Path
    extensions = {
        ".support": ("add_support", "support"),
        ".source":  ("add_source",  "sources"),
        ".what":    ("add_what",    "what"),
        ".why":     ("add_why",     "why"),
        ".how":     ("add_how",     "how"),
        ".when":    ("add_when",    "when"),
        ".where":   ("add_where",   "where"),
    }
    p = Premise(name="test")
    for ext, (_, attr) in extensions.items():
        f = tmp_path / f"test{ext}"
        f.write_text(f"Content for {attr}.")
        p.apply_file(f)
        assert getattr(p, attr) == [f"Content for {attr}."]


def test_apply_file_ignores_unknown_extension(tmp_path) -> None:
    """apply_file() silently ignores unknown file extensions."""
    from pathlib import Path
    f = tmp_path / "test.unknown"
    f.write_text("Should be ignored.")
    p = Premise(name="test")
    p.apply_file(f)
    assert p.statements == []
    assert p.support == []


def test_str_is_description() -> None:
    """String representation is description."""
    p = Premise(name="my claim", description="My claim description")
    assert str(p) == "My claim description"


def test_add_who() -> None:
    """add_who() populates the who list."""
    p = Premise(name="test")
    p.add_who("Scientists and public health officials")
    assert "Scientists and public health officials" in p.who


def test_who_round_trip_dict() -> None:
    """who field survives to_dict / from_dict."""
    p = Premise(name="test")
    p.add_who("Everyone")
    p2 = Premise.from_dict(p.to_dict())
    assert p2.who == ["Everyone"]


def test_who_loaded_from_file(tmp_path: Path) -> None:
    """apply_file dispatches .who extension to add_who."""
    who_file = tmp_path / "p.who"
    who_file.write_text("Affected parties\nExperts\n")
    p = Premise(name="p")
    p.apply_file(who_file)
    assert p.who == ["Affected parties", "Experts"]


def test_check_five_w_who(sample_arg: Argument) -> None:
    """_check_five_w returns who answer when 'who' is in user input."""
    from difficult_dialogs.policy import KnowItAllPolicy
    premise = sample_arg.premises[0]
    premise.add_who("All citizens")
    policy = KnowItAllPolicy(sample_arg)
    policy.start()
    policy.state.current_premise = premise.name
    response = policy.handle_input("who is affected by this")
    assert response == "All citizens"


# ---------------------------------------------------------------------------
# Premise.translations — i18n field
# ---------------------------------------------------------------------------

class TestPremiseTranslations:
    """Tests for Premise.translations and related helpers."""

    def _make_premise(self) -> "Premise":
        from difficult_dialogs.premises import Premise
        p = Premise(name="test")
        p.add_statement("Computers process information.")
        p.add_translation("es-ES", "statements", "Los ordenadores procesan información.")
        return p

    def test_add_translation_stored(self) -> None:
        p = self._make_premise()
        assert "es-ES" in p.translations
        assert "statements" in p.translations["es-ES"]
        assert "Los ordenadores procesan información." in p.translations["es-ES"]["statements"]

    def test_get_statements_default_lang(self) -> None:
        p = self._make_premise()
        stmts = p.get_statements()
        assert "Computers process information." in stmts

    def test_get_statements_translated(self) -> None:
        p = self._make_premise()
        stmts = p.get_statements(lang="es-ES")
        assert "Los ordenadores procesan información." in stmts

    def test_get_statements_falls_back_when_no_translation(self) -> None:
        p = self._make_premise()
        stmts = p.get_statements(lang="fr-FR")
        assert "Computers process information." in stmts

    def test_to_dict_includes_translations(self) -> None:
        p = self._make_premise()
        d = p.to_dict()
        assert "translations" in d
        assert "es-ES" in d["translations"]

    def test_from_dict_round_trip(self) -> None:
        from difficult_dialogs.premises import Premise
        p = self._make_premise()
        p2 = Premise.from_dict(p.to_dict())
        assert p2.translations == p.translations

    def test_to_dict_omits_translations_when_empty(self) -> None:
        from difficult_dialogs.premises import Premise
        p = Premise(name="plain")
        p.add_statement("Statement.")
        assert "translations" not in p.to_dict()

    def test_apply_file_locale_specific(self, tmp_path) -> None:
        """apply_file detects locale-specific filename pattern."""
        from difficult_dialogs.premises import Premise
        f = tmp_path / "my_premise.es-ES.premise"
        f.write_text("Una afirmación en español.")
        p = Premise(name="my_premise")
        p.apply_file(f)
        assert "es-ES" in p.translations
        assert "Una afirmación en español." in p.translations["es-ES"]["premise"]

    def test_apply_file_normal_not_affected(self, tmp_path) -> None:
        """Normal .premise files are not treated as locale-specific."""
        from difficult_dialogs.premises import Premise
        f = tmp_path / "my_premise.premise"
        f.write_text("Normal statement.")
        p = Premise(name="my_premise")
        p.apply_file(f)
        assert len(p.statements) == 1
        assert not p.translations
