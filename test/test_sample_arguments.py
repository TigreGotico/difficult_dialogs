"""Integration tests for all generated sample arguments."""
import pytest
from pathlib import Path
from difficult_dialogs.arguments import Argument
from difficult_dialogs.policy import KnowItAllPolicy


# Find all sample arguments automatically
SAMPLE_ARGS_DIR = Path(__file__).parent.parent / "examples" / "sample_arguments"


def discover_all_arguments() -> list[tuple[str, str, Path]]:
    """Discover all argument directories dynamically.
    
    Returns list of (category, topic_name, path) tuples.
    """
    discovered = []
    
    if not SAMPLE_ARGS_DIR.exists():
        return discovered
    
    for category_dir in sorted(SAMPLE_ARGS_DIR.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith("."):
            continue
        
        for topic_dir in sorted(category_dir.iterdir()):
            if not topic_dir.is_dir():
                continue
            
            # Check if this is a valid argument directory
            intro_file = topic_dir / "intro.dialog"
            if intro_file.exists():
                discovered.append((
                    category_dir.name,
                    topic_dir.name,
                    topic_dir
                ))
    
    return discovered


# Discover all arguments at module load time
ALL_ARGUMENTS = discover_all_arguments()


class TestSampleArgumentsDiscovery:
    """Test that we can discover all sample arguments."""
    
    def test_discovered_arguments(self) -> None:
        """Should discover all generated arguments."""
        assert len(ALL_ARGUMENTS) > 0, "No sample arguments found!"
        print(f"\nDiscovered {len(ALL_ARGUMENTS)} arguments across categories")
    
    def test_all_categories_present(self) -> None:
        """Should have arguments from all expected categories."""
        categories = set(cat for cat, _, _ in ALL_ARGUMENTS)
        expected_categories = {
            "technology", "science", "health", 
            "society", "philosophy", "education"
        }
        missing = expected_categories - categories
        assert not missing, f"Missing categories: {missing}"


class TestArgumentLoading:
    """Test that all generated arguments load correctly."""
    
    @pytest.mark.parametrize("category,topic,path", ALL_ARGUMENTS)
    def test_load_argument(self, category: str, topic: str, path: Path) -> None:
        """Load each argument and verify basic structure."""
        arg = Argument()
        arg.load(path)
        
        # Verify required fields
        assert arg.name, f"{category}/{topic}: Name is empty"
        assert arg.intro, f"{category}/{topic}: Intro is empty"
        assert arg.conclusion, f"{category}/{topic}: Conclusion is empty"
        assert len(arg.premises) > 0, f"{category}/{topic}: No premises loaded"
        
        # Verify name matches directory
        assert arg.name == topic.replace("_", " "), \
            f"{category}/{topic}: Name mismatch (expected '{topic.replace('_', ' ')}', got '{arg.name}')"
    
    @pytest.mark.parametrize("category,topic,path", ALL_ARGUMENTS)
    def test_premises_have_statements(self, category: str, topic: str, path: Path) -> None:
        """Each premise should have at least one statement."""
        arg = Argument().load(path)
        
        for premise in arg.premises:
            assert len(premise.statements) > 0, \
                f"{category}/{topic}/{premise.name}: Premise has no statements"
    
    @pytest.mark.parametrize("category,topic,path", ALL_ARGUMENTS)
    def test_minimum_premise_count(self, category: str, topic: str, path: Path) -> None:
        """Each argument should have at least 2 premises."""
        arg = Argument().load(path)
        
        assert len(arg.premises) >= 2, \
            f"{category}/{topic}: Too few premises ({len(arg.premises)}, expected >= 2)"


class TestArgumentIntegrity:
    """Test argument quality and consistency."""
    
    @pytest.mark.parametrize("category,topic,path", ALL_ARGUMENTS)
    def test_no_duplicate_premise_names(self, category: str, topic: str, path: Path) -> None:
        """Premise names should be unique within an argument."""
        arg = Argument().load(path)
        
        premise_names = [p.name for p in arg.premises]
        duplicates = [name for name in premise_names if premise_names.count(name) > 1]
        
        assert not duplicates, \
            f"{category}/{topic}: Duplicate premise names: {set(duplicates)}"
    
    @pytest.mark.parametrize("category,topic,path", ALL_ARGUMENTS)
    def test_intro_not_same_as_conclusion(self, category: str, topic: str, path: Path) -> None:
        """Intro and conclusion should be different."""
        arg = Argument().load(path)
        
        assert arg.intro.strip() != arg.conclusion.strip(), \
            f"{category}/{topic}: Intro and conclusion are identical"
    
    @pytest.mark.parametrize("category,topic,path", ALL_ARGUMENTS)
    def test_statement_uniqueness(self, category: str, topic: str, path: Path) -> None:
        """Statements within a premise should be unique."""
        arg = Argument().load(path)
        
        for premise in arg.premises:
            statements = [s.text for s in premise.statements]
            duplicates = [s for s in statements if statements.count(s) > 1]
            
            assert not duplicates, \
                f"{category}/{topic}/{premise.name}: Duplicate statements: {set(duplicates)}"


class TestDialogFlow:
    """Test that arguments work with dialog policies."""
    
    @pytest.mark.parametrize("category,topic,path", ALL_ARGUMENTS)
    def test_policy_initialization(self, category: str, topic: str, path: Path) -> None:
        """Policy should initialize successfully with the argument."""
        arg = Argument().load(path)
        policy = KnowItAllPolicy(arg)
        
        assert policy.argument is arg
        assert policy.start() == arg.intro
    
    @pytest.mark.parametrize("category,topic,path", ALL_ARGUMENTS)
    def test_has_statements_initially(self, category: str, topic: str, path: Path) -> None:
        """Policy should have statements to present at start."""
        arg = Argument().load(path)
        policy = KnowItAllPolicy(arg)
        
        # Check that there are statements available (internal method)
        next_stmt = policy._get_next_statement()
        assert next_stmt is not None, \
            f"{category}/{topic}: Policy has no statements at start"
    
    @pytest.mark.parametrize("category,topic,path", ALL_ARGUMENTS)
    def test_agree_path_completes(self, category: str, topic: str, path: Path) -> None:
        """Agreeing to all statements should complete the argument."""
        arg = Argument().load(path)
        policy = KnowItAllPolicy(arg)
        
        # Start the dialog
        policy.start()
        
        # Simulate agreeing to everything
        statements_spoken = 0
        max_iterations = len(arg.premises) * 5 + 10  # Safety limit
        
        for _ in range(max_iterations):
            next_stmt = policy._get_next_statement()
            if next_stmt is None:
                break
            
            premise_name, statement_text = next_stmt
            # Agree to this statement
            premise = arg.get_premise(premise_name)
            if premise:
                for stmt in premise.statements:
                    if stmt.text == statement_text:
                        stmt.agree()
            
            statements_spoken += 1
        
        # Should have gone through all premises
        assert statements_spoken >= len(arg.premises), \
            f"{category}/{topic}: Only spoke {statements_spoken} statements (expected >= {len(arg.premises)})"
    
    @pytest.mark.parametrize("category,topic,path", ALL_ARGUMENTS)
    def test_disagree_gets_response(self, category: str, topic: str, path: Path) -> None:
        """Disagreeing should get a response from policy."""
        arg = Argument().load(path)
        policy = KnowItAllPolicy(arg)
        
        # Disagree and check for response
        response = policy.handle_input("no")
        
        assert response is not None, \
            f"{category}/{topic}: No response to disagreement"
        assert len(response) > 0, \
            f"{category}/{topic}: Empty response to disagreement"


class TestFileStructure:
    """Test that file structure is correct."""
    
    @pytest.mark.parametrize("category,topic,path", ALL_ARGUMENTS)
    def test_required_files_exist(self, category: str, topic: str, path: Path) -> None:
        """Required files should exist in each argument directory."""
        required_files = ["intro.dialog", "conclusion.conclusion"]
        
        for filename in required_files:
            filepath = path / filename
            assert filepath.exists(), \
                f"{category}/{topic}: Missing required file: {filename}"
    
    @pytest.mark.parametrize("category,topic,path", ALL_ARGUMENTS)
    def test_premise_directories_have_descriptions(self, category: str, topic: str, path: Path) -> None:
        """Each premise directory should have description.premise file."""
        arg = Argument().load(path)
        
        for premise in arg.premises:
            premise_dir = path / premise.name
            description_file = premise_dir / "description.premise"
            
            assert description_file.exists(), \
                f"{category}/{topic}/{premise.name}: Missing description.premise"
    
    @pytest.mark.parametrize("category,topic,path", ALL_ARGUMENTS)
    def test_no_empty_files(self, category: str, topic: str, path: Path) -> None:
        """No files should be empty."""
        for file_path in path.rglob("*"):
            if file_path.is_file():
                content = file_path.read_text().strip()
                assert content, \
                    f"{category}/{topic}: Empty file: {file_path.relative_to(path)}"


class TestStatistics:
    """Collect and verify statistics about the argument library."""
    
    def test_total_argument_count(self) -> None:
        """Should have at least 30 arguments."""
        assert len(ALL_ARGUMENTS) >= 30, \
            f"Expected >= 30 arguments, found {len(ALL_ARGUMENTS)}"
    
    def test_arguments_per_category(self) -> None:
        """Each category should have at least 5 arguments."""
        category_counts: dict[str, int] = {}
        for cat, _, _ in ALL_ARGUMENTS:
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        for category, count in category_counts.items():
            assert count >= 5, \
                f"Category '{category}' has only {count} arguments (expected >= 5)"
    
    def test_average_premises_per_argument(self) -> None:
        """Average premises per argument should be >= 2."""
        total_premises = 0
        for _, _, path in ALL_ARGUMENTS:
            arg = Argument().load(path)
            total_premises += len(arg.premises)
        
        avg = total_premises / len(ALL_ARGUMENTS) if ALL_ARGUMENTS else 0
        assert avg >= 2, \
            f"Average premises per argument is {avg:.1f} (expected >= 2)"
        
        print(f"\nStatistics:")
        print(f"  Total arguments: {len(ALL_ARGUMENTS)}")
        print(f"  Total premises: {total_premises}")
        print(f"  Average premises/argument: {avg:.1f}")


if __name__ == "__main__":
    # Run with: pytest test/test_sample_arguments.py -v
    pytest.main([__file__, "-v"])
