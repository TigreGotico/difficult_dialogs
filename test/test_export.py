"""Tests for export functionality."""
import json
import pytest
import tempfile
from pathlib import Path
from difficult_dialogs.arguments import Argument
from difficult_dialogs.premises import Premise
from difficult_dialogs.export import (
    export_to_json,
    export_library_to_json,
    import_from_json,
    LibraryDatabase,
    export_to_sqlite,
)


@pytest.fixture
def sample_argument() -> Argument:
    """Create a sample argument for testing."""
    arg = Argument(
        name="Test Argument",
        intro="This is a test introduction.",
        conclusion="This is a test conclusion."
    )
    
    premise1 = Premise(name="premise_one")
    premise1.add_statement("Statement 1")
    premise1.add_statement("Statement 2")
    premise1.sources.append("http://example.com/source1")
    
    premise2 = Premise(name="premise_two")
    premise2.add_statement("Statement 3")
    premise2.support.append("Supporting evidence")
    
    arg.add_premise(premise1)
    arg.add_premise(premise2)
    
    return arg


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestJSONExport:
    """Test JSON export functionality."""
    
    def test_export_single_argument(self, sample_argument: Argument, temp_dir: Path) -> None:
        """Export single argument to JSON."""
        output_path = temp_dir / "test_arg.json"
        
        result_path = export_to_json(sample_argument, output_path)
        
        assert result_path.exists()
        assert result_path == output_path
        
        # Verify JSON structure
        with open(result_path) as f:
            data = json.load(f)
        
        assert data["name"] == "Test Argument"
        assert data["intro"] == "This is a test introduction."
        assert data["conclusion"] == "This is a test conclusion."
        assert len(data["premises"]) == 2
        assert "_export_info" in data
    
    def test_export_creates_parent_dirs(self, temp_dir: Path) -> None:
        """Export should create parent directories."""
        nested_path = temp_dir / "nested" / "path" / "output.json"
        
        arg = Argument(name="Test", intro="Intro", conclusion="Conclusion")
        result_path = export_to_json(arg, nested_path)
        
        assert result_path.exists()
        assert result_path.parent.exists()
    
    def test_roundtrip_import_export(self, sample_argument: Argument, temp_dir: Path) -> None:
        """Export then import should recreate argument."""
        output_path = temp_dir / "roundtrip.json"
        
        # Export
        export_to_json(sample_argument, output_path)
        
        # Import
        imported = import_from_json(output_path)
        
        assert isinstance(imported, Argument)
        assert imported.name == sample_argument.name
        assert imported.intro == sample_argument.intro
        assert imported.conclusion == sample_argument.conclusion
        assert len(imported.premises) == len(sample_argument.premises)


class TestLibraryBundle:
    """Test library bundle export."""
    
    def test_export_library_bundle(self, temp_dir: Path) -> None:
        """Export multiple arguments as bundle."""
        # Create test arguments
        args_dir = temp_dir / "arguments"
        args_dir.mkdir()
        
        # Create two test arguments
        for i in range(2):
            arg_dir = args_dir / f"argument_{i}"
            arg_dir.mkdir()
            
            arg = Argument(
                name=f"Argument {i}",
                intro=f"Intro {i}",
                conclusion=f"Conclusion {i}"
            )
            arg.add_premise(Premise(name="p1").add_statement("Statement"))
            
            # Save in file format
            (arg_dir / "intro.dialog").write_text(arg.intro)
            (arg_dir / "conclusion.conclusion").write_text(arg.conclusion)
            premise_dir = arg_dir / "p1"
            premise_dir.mkdir()
            (premise_dir / "description.premise").write_text("Statement")
        
        # Export bundle
        output_path = temp_dir / "library_bundle.json"
        result_path = export_library_to_json(args_dir, output_path)
        
        assert result_path.exists()
        
        # Verify bundle structure
        with open(result_path) as f:
            bundle = json.load(f)
        
        assert "_export_info" in bundle
        assert bundle["_export_info"]["format"] == "difficult_dialogs_library_bundle"
        assert len(bundle["arguments"]) == 2
    
    def test_import_bundle(self, temp_dir: Path) -> None:
        """Import library bundle."""
        # Create and export bundle
        args_dir = temp_dir / "arguments"
        args_dir.mkdir()
        
        arg_dir = args_dir / "test_arg"
        arg_dir.mkdir()
        
        arg = Argument(name="Test", intro="Intro", conclusion="Conclusion")
        arg.add_premise(Premise(name="p1").add_statement("Stmt"))
        
        (arg_dir / "intro.dialog").write_text(arg.intro)
        (arg_dir / "conclusion.conclusion").write_text(arg.conclusion)
        p1_dir = arg_dir / "p1"
        p1_dir.mkdir()
        (p1_dir / "description.premise").write_text("Stmt")
        
        bundle_path = temp_dir / "bundle.json"
        export_library_to_json(args_dir, bundle_path)
        
        # Import
        imported_args = import_from_json(bundle_path)
        
        assert isinstance(imported_args, list)
        assert len(imported_args) == 1
        # Name comes from exported data, will be lowercase with underscores
        assert imported_args[0].name in ["Test", "test arg"]
        assert imported_args[0].intro == "Intro"


class TestSQLiteDatabase:
    """Test SQLite database export."""
    
    def test_create_database(self, temp_dir: Path) -> None:
        """Create SQLite database."""
        db_path = temp_dir / "test.db"
        db = LibraryDatabase(db_path)
        
        assert db_path.exists()
        db.close()
    
    def test_add_and_retrieve_argument(self, sample_argument: Argument, temp_dir: Path) -> None:
        """Add argument to database and retrieve it."""
        db_path = temp_dir / "test.db"
        db = LibraryDatabase(db_path)

        arg_id = db.add_argument(sample_argument, category="test")
        assert arg_id > 0

        retrieved = db.get_argument("Test Argument")

        assert retrieved is not None
        assert retrieved.name == sample_argument.name
        assert len(retrieved.premises) == len(sample_argument.premises)
        assert retrieved.premises[0].name == "premise_one"
        assert len(retrieved.premises[0].statements) == 2

        db.close()

    def test_support_persisted_in_sqlite(self, temp_dir: Path) -> None:
        """Support arguments are stored and loaded from SQLite."""
        db_path = temp_dir / "test.db"
        db = LibraryDatabase(db_path)

        arg = Argument(name="Support Test", intro="Intro.", conclusion="Conclusion.")
        p = Premise(name="p1")
        p.add_statement("Main claim.")
        p.add_support("First fallback argument.")
        p.add_support("Second fallback argument.")
        arg.add_premise(p)

        db.add_argument(arg)
        retrieved = db.get_argument("Support Test")
        assert retrieved is not None
        rp = retrieved.get_premise("p1")
        assert rp is not None
        assert rp.support == ["First fallback argument.", "Second fallback argument."]
        db.close()

    def test_five_ws_persisted_in_sqlite(self, temp_dir: Path) -> None:
        """All Five-Ws fields are stored and loaded from SQLite."""
        db_path = temp_dir / "test.db"
        db = LibraryDatabase(db_path)

        arg = Argument(name="5W Test", intro="Intro.", conclusion="Conclusion.")
        p = Premise(name="p1")
        p.add_statement("Claim.")
        p.add_what("What it means.")
        p.add_why("Why it is true.")
        p.add_how("How it works.")
        p.add_when("When it applies.")
        p.add_where("Where observed.")
        arg.add_premise(p)

        db.add_argument(arg)
        retrieved = db.get_argument("5W Test")
        assert retrieved is not None
        rp = retrieved.get_premise("p1")
        assert rp is not None
        assert rp.what == ["What it means."]
        assert rp.why == ["Why it is true."]
        assert rp.how == ["How it works."]
        assert rp.when == ["When it applies."]
        assert rp.where == ["Where observed."]
        db.close()
    
    def test_list_arguments(self, temp_dir: Path) -> None:
        """List arguments in database."""
        db_path = temp_dir / "test.db"
        db = LibraryDatabase(db_path)
        
        # Add multiple arguments
        for i in range(3):
            arg = Argument(
                name=f"Argument {i}",
                intro="Intro",
                conclusion="Conclusion"
            )
            arg.add_premise(Premise(name="p1").add_statement("Stmt"))
            db.add_argument(arg, category="test")
        
        names = db.list_arguments()
        
        assert len(names) == 3
        assert "Argument 0" in names
        assert "Argument 1" in names
        assert "Argument 2" in names
        
        db.close()
    
    def test_get_statistics(self, temp_dir: Path) -> None:
        """Get database statistics."""
        db_path = temp_dir / "test.db"
        db = LibraryDatabase(db_path)
        
        # Add arguments with different categories
        for i, cat in enumerate(["cat1", "cat2", "cat1"]):
            arg = Argument(
                name=f"Arg{i}",
                intro="Intro",
                conclusion="Conclusion"
            )
            arg.add_premise(Premise(name="p1").add_statement("Stmt"))
            db.add_argument(arg, category=cat)
        
        stats = db.get_statistics()
        
        assert stats["total_arguments"] == 3
        assert "cat1" in stats["by_category"]
        assert stats["by_category"]["cat1"] == 2
        assert "cat2" in stats["by_category"]
        
        db.close()
    
    def test_validation_storage(self, sample_argument: Argument, temp_dir: Path) -> None:
        """Store and retrieve validation results."""
        db_path = temp_dir / "test.db"
        db = LibraryDatabase(db_path)
        
        # Add argument
        db.add_argument(sample_argument)
        
        # Add validation result
        db.add_validation_result(
            sample_argument.name,
            score=0.85,
            passed=True,
            issues_count=2
        )
        
        # Verify by getting stats
        stats = db.get_statistics()
        
        assert stats["validation"]["validated_count"] == 1
        assert stats["validation"]["average_score"] == 0.85
        
        db.close()


class TestExportToSQLite:
    """Test high-level SQLite export function."""
    
    def test_export_directory_to_sqlite(self, temp_dir: Path) -> None:
        """Export entire directory to SQLite."""
        # Create test arguments with unique directory names
        args_dir = temp_dir / "arguments"
        args_dir.mkdir()
        
        arg_count = 0
        for cat in ["tech", "science"]:
            cat_dir = args_dir / cat
            cat_dir.mkdir()
            
            for i in range(2):
                arg_dir = cat_dir / f"{cat}_arg_{i}"  # Unique dir name per category
                arg_dir.mkdir()
                
                arg = Argument(
                    name=f"{cat} arg {i}",
                    intro="Intro",
                    conclusion="Conclusion"
                )
                arg.add_premise(Premise(name="p1").add_statement("Stmt"))
                
                # Save in file format
                (arg_dir / "intro.dialog").write_text(arg.intro)
                (arg_dir / "conclusion.conclusion").write_text(arg.conclusion)
                p1_dir = arg_dir / "p1"
                p1_dir.mkdir()
                (p1_dir / "description.premise").write_text("Stmt")
                
                arg_count += 1
        
        # Export to SQLite
        db_path = temp_dir / "library.db"
        db = export_to_sqlite(args_dir, db_path, include_validation=False)
        
        # Verify
        stats = db.get_statistics()
        assert stats["total_arguments"] == arg_count  # Should match actual count
        
        db.close()


class TestExportCoverageBranches:
    """Cover remaining uncovered branches in export.py."""

    def test_json_encoder_fallback_for_unknown_type(self) -> None:
        """ArgumentJSONEncoder falls back to super().default() for unknown types."""
        from difficult_dialogs.export import ArgumentEncoder as ArgumentJSONEncoder
        import json

        encoder = ArgumentJSONEncoder()
        with pytest.raises(TypeError):
            encoder.default(object())

    def test_get_argument_returns_none_for_missing(self, temp_dir: Path) -> None:
        """get_argument() returns None when argument not in database."""
        db = LibraryDatabase(temp_dir / "test.db")
        result = db.get_argument("nonexistent_argument")
        assert result is None
        db.close()

    def test_list_arguments_with_category_filter(
        self, temp_dir: Path, sample_argument: Argument
    ) -> None:
        """list_arguments() filters by category when provided."""
        db = LibraryDatabase(temp_dir / "test.db")
        db.add_argument(sample_argument, category="science")

        arg2 = Argument(name="Other Arg", intro="I.", conclusion="C.")
        arg2.add_premise(Premise(name="p1").add_statement("s1"))
        db.add_argument(arg2, category="history")

        science_args = db.list_arguments(category="science")
        assert "Test Argument" in science_args
        assert "Other Arg" not in science_args
        db.close()

    def test_export_to_sqlite_with_validation(self, temp_dir: Path) -> None:
        """export_to_sqlite with include_validation=True runs validation."""
        from difficult_dialogs.export import export_to_sqlite

        args_dir = temp_dir / "args"
        args_dir.mkdir()
        arg_dir = args_dir / "my_arg"
        arg_dir.mkdir()

        arg = Argument(
            name="my arg",
            intro="This is a sufficiently long introduction for validation tests.",
            conclusion="This is a sufficiently long conclusion for validation tests.",
        )
        p = Premise(name="p1")
        p.add_statement("Statement one with enough length for validation.")
        p2 = Premise(name="p2")
        p2.add_statement("Statement two with enough length for validation.")
        arg.add_premise(p)
        arg.add_premise(p2)
        arg.save(arg_dir)

        db_path = temp_dir / "library.db"
        db = export_to_sqlite(args_dir, db_path, include_validation=True)
        stats = db.get_statistics()
        assert stats["total_arguments"] >= 1
        db.close()

    def test_export_library_json_skips_bad_dirs(self, temp_dir: Path) -> None:
        """export_library_to_json skips directories that fail to load."""
        args_dir = temp_dir / "args"
        args_dir.mkdir()

        # Valid argument
        good_dir = args_dir / "good"
        good_dir.mkdir()
        arg = Argument(name="Good Arg", intro="Intro.", conclusion="Conclusion.")
        arg.add_premise(Premise(name="p1").add_statement("s1"))
        arg.save(good_dir)

        # Bad directory: no intro.dialog, no valid structure
        bad_dir = args_dir / "bad_subdir"
        bad_dir.mkdir()
        (bad_dir / "junk.txt").write_text("not an argument")

        output_path = temp_dir / "library.json"
        result = export_library_to_json(args_dir, output_path)
        # Should succeed (bad dirs are silently skipped)
        assert output_path.exists()


    def test_get_argument_id_raises_on_miss(self, temp_dir: Path) -> None:
        """_get_argument_id raises KeyError when argument name not found."""
        db = LibraryDatabase(temp_dir / "test.db")
        with pytest.raises(KeyError, match="not found"):
            db._get_argument_id("nonexistent")
        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestExportToMarkdown:
    """Tests for export_to_markdown."""

    def test_basic_structure(self, sample_argument: Argument) -> None:
        """Markdown contains title, intro, premises, and conclusion."""
        from difficult_dialogs.export import export_to_markdown
        md = export_to_markdown(sample_argument)
        assert "# Test Argument" in md
        assert "This is a test introduction." in md
        assert "## Premises" in md
        assert "## Conclusion" in md
        assert "This is a test conclusion." in md

    def test_premise_statements_listed(self, sample_argument: Argument) -> None:
        """Each statement appears as a list item."""
        from difficult_dialogs.export import export_to_markdown
        md = export_to_markdown(sample_argument)
        assert "- Statement 1" in md
        assert "- Statement 2" in md

    def test_five_ws_included(self) -> None:
        """Five-Ws fields appear when populated."""
        from difficult_dialogs.export import export_to_markdown
        arg = Argument(name="test", intro="I.", conclusion="C.")
        p = Premise(name="p1")
        p.add_statement("s1")
        p.add_what("A thing.")
        p.add_why("Because.")
        p.add_how("Like this.")
        p.add_when("Now.")
        p.add_where("Here.")
        arg.add_premise(p)
        md = export_to_markdown(arg)
        assert "**What:** A thing." in md
        assert "**Why:** Because." in md
        assert "**How:** Like this." in md
        assert "**When:** Now." in md
        assert "**Where:** Here." in md

    def test_sources_and_support_included(self) -> None:
        """Sources and support lines appear in the output."""
        from difficult_dialogs.export import export_to_markdown
        arg = Argument(name="test", intro="I.", conclusion="C.")
        p = Premise(name="p1")
        p.add_statement("s1")
        p.add_source("https://example.com")
        p.add_support("Because reasons.")
        arg.add_premise(p)
        md = export_to_markdown(arg)
        assert "https://example.com" in md
        assert "Because reasons." in md

    def test_writes_file(self, tmp_path: Path) -> None:
        """Passing output_path writes the file."""
        from difficult_dialogs.export import export_to_markdown
        arg = Argument(name="file test", intro="I.", conclusion="C.")
        out = tmp_path / "out.md"
        result = export_to_markdown(arg, out)
        assert out.exists()
        assert out.read_text() == result

    def test_no_path_returns_string_only(self, sample_argument: Argument) -> None:
        """Without output_path, no file is written and a string is returned."""
        from difficult_dialogs.export import export_to_markdown
        result = export_to_markdown(sample_argument)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_empty_argument(self) -> None:
        """Minimal argument (no premises) renders without error."""
        from difficult_dialogs.export import export_to_markdown
        arg = Argument(name="empty")
        md = export_to_markdown(arg)
        assert "# Empty" in md
