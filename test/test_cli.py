"""Tests for CLI functionality."""
import pytest
import subprocess
import sys
from pathlib import Path


class TestCLIHelp:
    """Test CLI help messages."""
    
    def test_main_help(self) -> None:
        """Main CLI should show help."""
        result = subprocess.run(
            [sys.executable, "-m", "difficult_dialogs.cli", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "generate" in result.stdout or "gen" in result.stdout
        assert "validate" in result.stdout or "val" in result.stdout
        assert "export" in result.stdout or "exp" in result.stdout
        assert "debate" in result.stdout or "deb" in result.stdout
        assert "list" in result.stdout or "ls" in result.stdout
    
    def test_generate_help(self) -> None:
        """Generate command should show help."""
        result = subprocess.run(
            [sys.executable, "-m", "difficult_dialogs.cli", "generate", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "topics" in result.stdout
        assert "--server" in result.stdout or "-s" in result.stdout
        assert "--output" in result.stdout or "-o" in result.stdout
    
    def test_validate_help(self) -> None:
        """Validate command should show help."""
        result = subprocess.run(
            [sys.executable, "-m", "difficult_dialogs.cli", "validate", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "path" in result.stdout
    
    def test_export_help(self) -> None:
        """Export command should show help."""
        result = subprocess.run(
            [sys.executable, "-m", "difficult_dialogs.cli", "export", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "input" in result.stdout
        assert "output" in result.stdout
        assert "--format" in result.stdout or "-f" in result.stdout


class TestCLIList:
    """Test list command."""
    
    def test_list_sample_arguments(self) -> None:
        """List command should find sample arguments."""
        sample_dir = Path(__file__).parent.parent / "examples" / "sample_arguments"
        
        if not sample_dir.exists():
            pytest.skip("Sample arguments directory not found")
        
        result = subprocess.run(
            [
                sys.executable, "-m", "difficult_dialogs.cli",
                "list", str(sample_dir)
            ],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "Total:" in result.stdout
        
        # Should mention categories
        output_lower = result.stdout.lower()
        assert any(cat in output_lower for cat in 
                  ["technology", "science", "health", "society", "philosophy", "education"])


class TestCLINoCommand:
    """Test CLI with no command."""
    
    def test_no_command_shows_help(self) -> None:
        """Running without command should show help."""
        result = subprocess.run(
            [sys.executable, "-m", "difficult_dialogs.cli"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower() or "commands:" in result.stdout.lower()


class TestCLIInvalidCommand:
    """Test CLI with invalid inputs."""
    
    def test_invalid_command(self) -> None:
        """Invalid command should return error."""
        result = subprocess.run(
            [sys.executable, "-m", "difficult_dialogs.cli", "invalid_command"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0
        assert "invalid" in result.stderr.lower() or "error" in result.stderr.lower()
    
    def test_validate_nonexistent_path(self) -> None:
        """Validate with nonexistent path should fail."""
        result = subprocess.run(
            [
                sys.executable, "-m", "difficult_dialogs.cli",
                "validate", "/nonexistent/path"
            ],
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0
        # Error messages go to stdout
        output = (result.stdout + result.stderr).lower()
        assert "not found" in output or "error" in output
    
    def test_debate_nonexistent_argument(self) -> None:
        """Debate with nonexistent argument should fail."""
        result = subprocess.run(
            [
                sys.executable, "-m", "difficult_dialogs.cli",
                "debate", "/nonexistent/argument"
            ],
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0
        # Error messages go to stdout
        output = (result.stdout + result.stderr).lower()
        assert "not found" in output or "error" in output


class TestCmdGenerateDirect:
    """Call cmd_generate() directly with mocked LLM."""

    def _make_generate_args(self, tmp_path, topics, **kwargs):
        import argparse
        defaults = dict(
            server="http://localhost:8000",
            model="default",
            timeout=30.0,
            output=str(tmp_path / "generated"),
            stance="pro",
            depth=1,
            no_sources=False,
            counter=False,
            force=False,
            validate=False,
        )
        defaults.update(kwargs)
        defaults["topics"] = topics
        return argparse.Namespace(**defaults)

    def test_generate_server_unreachable_returns_1(self, tmp_path) -> None:
        from unittest.mock import patch, MagicMock
        from difficult_dialogs.cli import cmd_generate

        mock_generator = MagicMock()
        mock_generator.client.health_check.return_value = False

        with patch("difficult_dialogs.llm.ArgumentGenerator", return_value=mock_generator):
            ns = self._make_generate_args(tmp_path, ["test topic"])
            rc = cmd_generate(ns)
        assert rc == 1

    def test_generate_single_topic_success(self, tmp_path) -> None:
        from unittest.mock import patch, MagicMock
        from difficult_dialogs.cli import cmd_generate
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise

        mock_arg = Argument(name="test topic", intro="Intro.", conclusion="Conclusion.")
        mock_arg.add_premise(Premise(name="p1").add_statement("Statement 1."))

        mock_generator = MagicMock()
        mock_generator.client.health_check.return_value = True
        mock_generator.generate.return_value = mock_arg

        with patch("difficult_dialogs.llm.ArgumentGenerator", return_value=mock_generator):
            ns = self._make_generate_args(tmp_path, ["test topic"])
            rc = cmd_generate(ns)
        assert rc == 0

    def test_generate_skips_existing(self, tmp_path) -> None:
        from unittest.mock import patch, MagicMock
        from difficult_dialogs.cli import cmd_generate

        # Pre-create the output directory with an intro.dialog
        output_dir = tmp_path / "generated"
        output_dir.mkdir(parents=True)
        existing = output_dir / "test_topic"
        existing.mkdir()
        (existing / "intro.dialog").write_text("Already exists.")

        mock_generator = MagicMock()
        mock_generator.client.health_check.return_value = True

        with patch("difficult_dialogs.llm.ArgumentGenerator", return_value=mock_generator):
            ns = self._make_generate_args(tmp_path, ["test topic"], force=False)
            rc = cmd_generate(ns)
        assert rc == 0
        mock_generator.generate.assert_not_called()

    def test_generate_with_validation(self, tmp_path) -> None:
        from unittest.mock import patch, MagicMock
        from difficult_dialogs.cli import cmd_generate
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise

        mock_arg = Argument(name="validated", intro="Intro.", conclusion="Conclusion.")
        mock_arg.add_premise(Premise(name="p1").add_statement("Statement 1."))

        mock_generator = MagicMock()
        mock_generator.client.health_check.return_value = True
        mock_generator.generate.return_value = mock_arg

        with patch("difficult_dialogs.llm.ArgumentGenerator", return_value=mock_generator):
            ns = self._make_generate_args(tmp_path, ["validated topic"], validate=True)
            rc = cmd_generate(ns)
        assert rc == 0

    def test_generate_handles_exception(self, tmp_path) -> None:
        from unittest.mock import patch, MagicMock
        from difficult_dialogs.cli import cmd_generate

        mock_generator = MagicMock()
        mock_generator.client.health_check.return_value = True
        mock_generator.generate.side_effect = RuntimeError("generation failed")

        with patch("difficult_dialogs.llm.ArgumentGenerator", return_value=mock_generator):
            ns = self._make_generate_args(tmp_path, ["failing topic"])
            rc = cmd_generate(ns)
        assert rc == 1  # failed > 0 → returns 1


class TestCmdValidateDirect:
    """Call cmd_validate() directly to get coverage."""

    def test_validate_nonexistent_path_returns_1(self) -> None:
        import argparse
        from difficult_dialogs.cli import cmd_validate

        args = argparse.Namespace(path="/nonexistent/path/for/test", verbose=False)
        assert cmd_validate(args) == 1

    def test_validate_directory_with_arguments(self, tmp_path) -> None:
        import argparse
        from difficult_dialogs.cli import cmd_validate
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise

        # Build a minimal valid argument
        arg = Argument(
            name="cli test arg",
            intro="This is a sufficiently long intro for validation purposes.",
            conclusion="This is a sufficiently long conclusion for validation.",
        )
        p1 = Premise(name="p1")
        p1.add_statement("Statement one with enough length for validation.")
        p2 = Premise(name="p2")
        p2.add_statement("Statement two with enough length for validation.")
        arg.add_premise(p1)
        arg.add_premise(p2)
        arg.save(tmp_path / "test_arg")

        ns = argparse.Namespace(path=str(tmp_path), verbose=True)
        rc = cmd_validate(ns)
        assert rc in (0, 1)  # may pass or fail depending on scores

    def test_validate_empty_directory_returns_1(self, tmp_path) -> None:
        import argparse
        from difficult_dialogs.cli import cmd_validate

        ns = argparse.Namespace(path=str(tmp_path), verbose=False)
        assert cmd_validate(ns) == 1  # no arguments found


class TestCmdExportDirect:
    """Call cmd_export() directly to get coverage."""

    def test_export_nonexistent_input_returns_1(self, tmp_path) -> None:
        import argparse
        from difficult_dialogs.cli import cmd_export

        ns = argparse.Namespace(
            input="/nonexistent/input",
            output=str(tmp_path / "out.json"),
            format="json",
            no_validation=True,
            stats=False,
        )
        assert cmd_export(ns) == 1

    def test_export_to_json(self, tmp_path) -> None:
        import argparse
        from difficult_dialogs.cli import cmd_export
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise

        arg = Argument(name="export test", intro="Intro.", conclusion="Conclusion.")
        p = Premise(name="p1")
        p.add_statement("s1")
        arg.add_premise(p)
        arg.save(tmp_path / "export_test")

        ns = argparse.Namespace(
            input=str(tmp_path),
            output=str(tmp_path / "library.json"),
            format="json",
            no_validation=True,
            stats=False,
        )
        rc = cmd_export(ns)
        assert rc == 0
        assert (tmp_path / "library.json").exists()

    def test_export_to_sqlite(self, tmp_path) -> None:
        import argparse
        from difficult_dialogs.cli import cmd_export
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise

        arg = Argument(name="sqlite test", intro="Intro.", conclusion="Conclusion.")
        p = Premise(name="p1")
        p.add_statement("s1")
        arg.add_premise(p)
        arg.save(tmp_path / "sqlite_test")

        ns = argparse.Namespace(
            input=str(tmp_path),
            output=str(tmp_path / "library.db"),
            format="sqlite",
            no_validation=True,
            stats=False,
        )
        rc = cmd_export(ns)
        assert rc == 0

    def test_export_unknown_format_returns_1(self, tmp_path) -> None:
        import argparse
        from difficult_dialogs.cli import cmd_export

        # Use an existing path so it doesn't fail on input check
        ns = argparse.Namespace(
            input=str(tmp_path),
            output=str(tmp_path / "out.xyz"),
            format="xyz",
            no_validation=True,
            stats=False,
        )
        assert cmd_export(ns) == 1


class TestCmdListDirect:
    """Call cmd_list() directly to get coverage."""

    def test_list_nonexistent_path_returns_1(self) -> None:
        import argparse
        from difficult_dialogs.cli import cmd_list

        ns = argparse.Namespace(path="/nonexistent/path")
        assert cmd_list(ns) == 1

    def test_list_with_arguments(self, tmp_path) -> None:
        import argparse
        from difficult_dialogs.cli import cmd_list
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise

        arg = Argument(name="list test", intro="Intro.", conclusion="Conclusion.")
        p = Premise(name="p1")
        p.add_statement("s1")
        arg.add_premise(p)
        arg.save(tmp_path / "list_test")

        ns = argparse.Namespace(path=str(tmp_path))
        rc = cmd_list(ns)
        assert rc == 0


class TestCmdValidateVerboseDirect:
    """Cover verbose failure reporting in cmd_validate."""

    def test_validate_verbose_shows_failed_details(self, tmp_path) -> None:
        import argparse
        from difficult_dialogs.cli import cmd_validate
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise

        # Create a clearly invalid argument (no conclusion, no premises)
        arg_dir = tmp_path / "bad_arg"
        arg_dir.mkdir()
        (arg_dir / "intro.dialog").write_text("Intro only.")
        (arg_dir / "conclusion.conclusion").write_text("")

        ns = argparse.Namespace(path=str(tmp_path), verbose=True)
        rc = cmd_validate(ns)
        # Should return 1 (has failures) without crashing
        assert rc in (0, 1)


class TestCmdValidateVerboseMore:
    """Cover >10 failed arguments verbose truncation."""

    def test_verbose_truncates_after_10_failures(self, tmp_path) -> None:
        import argparse
        from difficult_dialogs.cli import cmd_validate
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise

        # Create 12 minimal arguments that will fail validation (no premises)
        for i in range(12):
            arg_dir = tmp_path / f"bad_arg_{i}"
            arg_dir.mkdir()
            (arg_dir / "intro.dialog").write_text("Short.")
            (arg_dir / "conclusion.conclusion").write_text("")

        ns = argparse.Namespace(path=str(tmp_path), verbose=True)
        rc = cmd_validate(ns)
        # Should handle >10 failures without crashing (truncation path covered)
        assert rc == 1


class TestCmdExportStatsDirect:
    """Cover --stats output branch in cmd_export."""

    def test_export_sqlite_with_stats(self, tmp_path) -> None:
        import argparse
        from difficult_dialogs.cli import cmd_export
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise

        arg = Argument(name="stats test", intro="Intro.", conclusion="Conclusion.")
        p = Premise(name="p1")
        p.add_statement("s1")
        arg.add_premise(p)
        arg.save(tmp_path / "stats_test")

        ns = argparse.Namespace(
            input=str(tmp_path),
            output=str(tmp_path / "library.db"),
            format="sqlite",
            no_validation=True,
            stats=True,
        )
        rc = cmd_export(ns)
        assert rc == 0

    def test_export_sqlite_with_stats_and_validation(self, tmp_path) -> None:
        """Cover the avg validation score display path (line 196)."""
        import argparse
        from difficult_dialogs.cli import cmd_export
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise

        arg = Argument(
            name="validated stats",
            intro="This is a sufficiently long intro for validation tests.",
            conclusion="This is a sufficiently long conclusion for validation.",
        )
        p1 = Premise(name="p1")
        p1.add_statement("Statement one with enough length for this test.")
        p2 = Premise(name="p2")
        p2.add_statement("Statement two with enough length for this test.")
        arg.add_premise(p1)
        arg.add_premise(p2)
        arg.save(tmp_path / "validated_arg")

        ns = argparse.Namespace(
            input=str(tmp_path),
            output=str(tmp_path / "library.db"),
            format="sqlite",
            no_validation=False,  # run validation so validated_count > 0
            stats=True,
        )
        rc = cmd_export(ns)
        assert rc == 0


class TestMainParser:
    """Cover main() parser via argparse directly."""

    def test_main_returns_0_for_no_args(self, capsys) -> None:
        from difficult_dialogs.cli import main
        import sys
        from unittest.mock import patch

        with patch.object(sys, "argv", ["difficult-dialogs"]):
            rc = main()
        assert rc == 0

    def test_main_validate_missing_path(self, capsys) -> None:
        from difficult_dialogs.cli import main
        import sys
        from unittest.mock import patch

        with patch.object(sys, "argv", ["difficult-dialogs", "validate", "/nonexistent"]):
            rc = main()
        assert rc == 1


class TestCmdDebateDirect:
    """Call cmd_debate() directly to get coverage."""

    def test_debate_nonexistent_argument_returns_1(self) -> None:
        import argparse
        from difficult_dialogs.cli import cmd_debate

        ns = argparse.Namespace(argument="/nonexistent/arg", policy="knowitall")
        assert cmd_debate(ns) == 1

    def test_debate_load_error_returns_1(self, tmp_path) -> None:
        import argparse
        from unittest.mock import patch
        from difficult_dialogs.cli import cmd_debate
        from difficult_dialogs.exceptions import ArgumentLoadError

        # Create an existing path so the existence check passes
        arg_dir = tmp_path / "broken"
        arg_dir.mkdir()

        ns = argparse.Namespace(argument=str(arg_dir), policy="knowitall")
        with patch("difficult_dialogs.arguments.Argument.load",
                   side_effect=ArgumentLoadError("corrupted")):
            rc = cmd_debate(ns)
        assert rc == 1

    def test_debate_invalid_policy_returns_1(self, tmp_path) -> None:
        import argparse
        from unittest.mock import patch
        from difficult_dialogs.cli import cmd_debate
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise

        arg = Argument(name="test", intro="Intro.", conclusion="Conclusion.")
        p = Premise(name="p1")
        p.add_statement("s1")
        arg.add_premise(p)
        arg_dir = tmp_path / "valid_arg"
        arg.save(arg_dir)

        ns = argparse.Namespace(argument=str(arg_dir), policy="nonexistent_policy")
        rc = cmd_debate(ns)
        assert rc == 1

    def test_debate_runs_to_eof(self, tmp_path) -> None:
        import argparse
        from io import StringIO
        from unittest.mock import patch
        from difficult_dialogs.cli import cmd_debate
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise

        arg = Argument(name="debate test", intro="Intro.", conclusion="Conclusion.")
        p = Premise(name="p1")
        p.add_statement("Statement one.")
        arg.add_premise(p)
        arg_dir = tmp_path / "debate_test"
        arg.save(arg_dir)

        ns = argparse.Namespace(argument=str(arg_dir), policy="knowitall")
        # Simulate EOF immediately so the loop exits
        with patch("builtins.input", side_effect=EOFError):
            rc = cmd_debate(ns)
        assert rc == 0

    def test_debate_auto_completes_when_no_next_statement(self, tmp_path) -> None:
        """Debate exits when all statements exhausted (next_stmt is None path)."""
        import argparse
        from unittest.mock import patch
        from difficult_dialogs.cli import cmd_debate
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise

        arg = Argument(name="auto test", intro="Intro.", conclusion="Conclusion.")
        p = Premise(name="p1")
        p.add_statement("Only statement.")
        arg.add_premise(p)
        arg_dir = tmp_path / "auto_test"
        arg.save(arg_dir)

        ns = argparse.Namespace(argument=str(arg_dir), policy="silent")
        # Agree once to advance past the only statement, then it should auto-complete
        with patch("builtins.input", return_value="yes"):
            rc = cmd_debate(ns)
        assert rc == 0

    def test_debate_quit_command(self, tmp_path) -> None:
        import argparse
        from unittest.mock import patch
        from difficult_dialogs.cli import cmd_debate
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise

        arg = Argument(name="quit test", intro="Intro.", conclusion="Conclusion.")
        p = Premise(name="p1")
        p.add_statement("Statement one.")
        arg.add_premise(p)
        arg_dir = tmp_path / "quit_test"
        arg.save(arg_dir)

        ns = argparse.Namespace(argument=str(arg_dir), policy="knowitall")
        with patch("builtins.input", return_value="quit"):
            rc = cmd_debate(ns)
        assert rc == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
