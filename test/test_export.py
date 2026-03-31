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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
