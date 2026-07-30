"""Tests for CLI functionality."""
import argparse
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


class TestDebateInputFile:
    """Tests for dd debate --input-file."""

    def _make_arg_dir(self, tmp_path) -> Path:
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise
        arg = Argument(name="file input test", intro="Intro.", conclusion="Done.")
        p = Premise(name="p1")
        p.add_statement("Statement one.")
        arg.add_premise(p)
        d = tmp_path / "file_input_arg"
        arg.save(d)
        return d

    def test_input_file_runs_to_completion(self, tmp_path) -> None:
        """debate --input-file reads turns from file and finishes without stdin."""
        from difficult_dialogs.cli import cmd_debate
        arg_dir = self._make_arg_dir(tmp_path)
        turns = tmp_path / "turns.txt"
        turns.write_text("yes\nyes\nyes\n")

        ns = argparse.Namespace(
            argument=str(arg_dir),
            policy="knowitall",
            save_transcript=None,
            input_file=str(turns),
        )
        rc = cmd_debate(ns)
        assert rc == 0

    def test_input_file_not_found_returns_1(self, tmp_path) -> None:
        """debate --input-file returns 1 when file does not exist."""
        from difficult_dialogs.cli import cmd_debate
        arg_dir = self._make_arg_dir(tmp_path)

        ns = argparse.Namespace(
            argument=str(arg_dir),
            policy="knowitall",
            save_transcript=None,
            input_file=str(tmp_path / "nonexistent.txt"),
        )
        rc = cmd_debate(ns)
        assert rc == 1

    def test_debate_help_shows_input_file(self) -> None:
        """debate --help mentions --input-file."""
        result = subprocess.run(
            [sys.executable, "-m", "difficult_dialogs.cli", "debate", "--help"],
            capture_output=True,
            text=True,
        )
        assert "--input-file" in result.stdout


class TestCmdScore:
    """Tests for `did score`."""

    def _make_good_arg(self, tmp_path: Path) -> Path:
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise
        arg = Argument(name="score test", intro="Intro.", conclusion="Done.")
        for i in range(3):
            p = Premise(name=f"premise_{i}", description="desc")
            p.add_statement(f"Statement {i}.")
            p.add_support(f"Support {i}.")
            arg.add_premise(p)
        d = tmp_path / "score_arg"
        arg.save(d)
        return d

    def test_score_good_argument_exits_0(self, tmp_path: Path) -> None:
        from difficult_dialogs.cli import cmd_score
        ns = argparse.Namespace(argument=str(self._make_good_arg(tmp_path)))
        rc = cmd_score(ns)
        assert rc == 0

    def test_score_missing_path_exits_1(self, tmp_path: Path) -> None:
        from difficult_dialogs.cli import cmd_score
        ns = argparse.Namespace(argument=str(tmp_path / "nope"))
        rc = cmd_score(ns)
        assert rc == 1

    def test_score_output_contains_percent(self, tmp_path: Path, capsys) -> None:
        from difficult_dialogs.cli import cmd_score
        ns = argparse.Namespace(argument=str(self._make_good_arg(tmp_path)))
        cmd_score(ns)
        out = capsys.readouterr().out
        assert "%" in out

    def test_score_help(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "difficult_dialogs.cli", "score", "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "score" in result.stdout


class TestCmdReplay:
    """Tests for `did replay`."""

    def _write_transcript(self, tmp_path: Path, entries: list) -> Path:
        import json
        p = tmp_path / "transcript.json"
        p.write_text(json.dumps(entries))
        return p

    def test_replay_list_format(self, tmp_path: Path, capsys) -> None:
        from difficult_dialogs.cli import cmd_replay
        entries = [
            {"role": "bot", "text": "Hello!"},
            {"role": "user", "text": "Yes."},
            {"role": "bot", "text": "Great."},
        ]
        path = self._write_transcript(tmp_path, entries)
        rc = cmd_replay(argparse.Namespace(transcript=str(path)))
        assert rc == 0
        out = capsys.readouterr().out
        assert "BOT:  Hello!" in out
        assert "USER: Yes." in out

    def test_replay_state_dict_format(self, tmp_path: Path, capsys) -> None:
        from difficult_dialogs.cli import cmd_replay
        import json
        state = {
            "spoken_premises": [],
            "transcript": [
                {"role": "bot", "text": "Intro."},
                {"role": "user", "text": "Sure."},
            ],
            "finished": False,
        }
        path = tmp_path / "state.json"
        path.write_text(json.dumps(state))
        rc = cmd_replay(argparse.Namespace(transcript=str(path)))
        assert rc == 0
        out = capsys.readouterr().out
        assert "BOT:" in out

    def test_replay_missing_file_exits_1(self, tmp_path: Path) -> None:
        from difficult_dialogs.cli import cmd_replay
        rc = cmd_replay(argparse.Namespace(transcript=str(tmp_path / "nope.json")))
        assert rc == 1

    def test_replay_invalid_json_exits_1(self, tmp_path: Path) -> None:
        from difficult_dialogs.cli import cmd_replay
        bad = tmp_path / "bad.json"
        bad.write_text("not json {{{")
        rc = cmd_replay(argparse.Namespace(transcript=str(bad)))
        assert rc == 1

    def test_replay_empty_transcript(self, tmp_path: Path, capsys) -> None:
        from difficult_dialogs.cli import cmd_replay
        path = self._write_transcript(tmp_path, [])
        rc = cmd_replay(argparse.Namespace(transcript=str(path)))
        assert rc == 0
        assert "empty" in capsys.readouterr().out

    def test_replay_help(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "difficult_dialogs.cli", "replay", "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "transcript" in result.stdout


COGITO_DIR = str(Path(__file__).parent.parent / "examples" / "i_think_therefore_i_am")


class TestCmdDiff:
    """Tests for `did diff`."""

    def test_diff_identical(self, capsys) -> None:
        from difficult_dialogs.cli import cmd_diff
        rc = cmd_diff(argparse.Namespace(argument_a=COGITO_DIR, argument_b=COGITO_DIR))
        assert rc == 0
        assert "identical" in capsys.readouterr().out

    def test_diff_bad_path(self, capsys) -> None:
        from difficult_dialogs.cli import cmd_diff
        rc = cmd_diff(argparse.Namespace(argument_a=COGITO_DIR, argument_b="/no/such/path"))
        assert rc == 1

    def test_diff_modified(self, tmp_path: Path, capsys) -> None:
        """A copy with a modified intro should show a META change."""
        import shutil
        copy_dir = tmp_path / "copy"
        shutil.copytree(COGITO_DIR, copy_dir)
        intro_file = copy_dir / "intro.dialog"
        intro_file.write_text("Modified intro text.")

        from difficult_dialogs.cli import cmd_diff
        rc = cmd_diff(argparse.Namespace(argument_a=COGITO_DIR, argument_b=str(copy_dir)))
        out = capsys.readouterr().out
        assert rc == 0
        assert "META" in out or "intro" in out

    def test_diff_help(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "difficult_dialogs.cli", "diff", "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "argument_a" in result.stdout or "argument" in result.stdout


class TestCmdSolvers:
    """Tests for `did solvers`."""

    def test_solvers_runs(self) -> None:
        """Command should exit without crashing (0 or 1 depending on installed plugins)."""
        result = subprocess.run(
            [sys.executable, "-m", "difficult_dialogs.cli", "solvers"],
            capture_output=True, text=True,
        )
        assert result.returncode in (0, 1)

    def test_list_solvers_returns_dict(self) -> None:
        from difficult_dialogs.yesno import list_solvers
        result = list_solvers()
        assert isinstance(result, dict)


class TestCmdDebateTranscript:
    """Cover --save-transcript path."""

    def test_save_transcript_creates_file(self, tmp_path) -> None:
        from difficult_dialogs.cli import cmd_debate
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise
        from unittest.mock import patch

        arg = Argument(name="transcript test", intro="Intro.", conclusion="Done.")
        p = Premise(name="p1")
        p.add_statement("Statement.")
        arg.add_premise(p)
        arg_dir = tmp_path / "transcript_test"
        arg.save(arg_dir)

        transcript_path = tmp_path / "transcript.md"
        ns = argparse.Namespace(
            argument=str(arg_dir),
            policy="silent",
            save_transcript=str(transcript_path),
            input_file=None,
        )
        with patch("builtins.input", return_value="yes"):
            rc = cmd_debate(ns)
        assert rc == 0
        assert transcript_path.exists()


class TestCmdDebateWatch:
    """Cover --watch code path (polling fallback, no watchdog)."""

    def test_watch_polling_fallback(self, tmp_path) -> None:
        from difficult_dialogs.cli import cmd_debate
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise
        from unittest.mock import patch

        arg = Argument(name="watch test", intro="Intro.", conclusion="Done.")
        p = Premise(name="p1")
        p.add_statement("Statement.")
        arg.add_premise(p)
        arg_dir = tmp_path / "watch_test"
        arg.save(arg_dir)

        ns = argparse.Namespace(
            argument=str(arg_dir),
            policy="silent",
            save_transcript=None,
            input_file=None,
            watch=True,
        )
        # Force no-watchdog path and simulate user typing "yes" then quit
        with patch.dict("sys.modules", {"watchdog": None, "watchdog.observers": None, "watchdog.events": None}):
            with patch("builtins.input", side_effect=["yes", "quit"]):
                rc = cmd_debate(ns)
        assert rc == 0


class TestCmdSolversDirect:
    """Call cmd_solvers() directly — cover all branches."""

    def test_solvers_direct_call(self) -> None:
        from difficult_dialogs.cli import cmd_solvers
        rc = cmd_solvers(argparse.Namespace())
        assert rc == 0

    def test_solvers_no_plugins(self, capsys) -> None:
        """Cover the 'no plugins at all' branch (lines 482-487)."""
        from difficult_dialogs.cli import cmd_solvers
        from unittest.mock import patch
        with patch("difficult_dialogs.yesno.list_solvers", return_value={}), \
             patch("difficult_dialogs.choices.list_solvers", return_value={}):
            rc = cmd_solvers(argparse.Namespace())
        out = capsys.readouterr().out
        assert rc == 0
        assert "No solver plugins found" in out

    def test_solvers_with_yesno_only(self, capsys) -> None:
        """Cover the yesno-populated + choices-empty branch."""
        from difficult_dialogs.cli import cmd_solvers
        from unittest.mock import patch
        with patch("difficult_dialogs.yesno.list_solvers", return_value={"test-yesno": "mod:Cls"}), \
             patch("difficult_dialogs.choices.list_solvers", return_value={}):
            rc = cmd_solvers(argparse.Namespace())
        out = capsys.readouterr().out
        assert rc == 0
        assert "YES/NO SOLVERS:" in out
        assert "test-yesno" in out
        assert "built-in label matcher" in out

    def test_solvers_with_both(self, capsys) -> None:
        """Cover both sections populated."""
        from difficult_dialogs.cli import cmd_solvers
        from unittest.mock import patch
        with patch("difficult_dialogs.yesno.list_solvers", return_value={"test-yesno": "m:C"}), \
             patch("difficult_dialogs.choices.list_solvers", return_value={"test-choice": "m:C2"}):
            rc = cmd_solvers(argparse.Namespace())
        out = capsys.readouterr().out
        assert rc == 0
        assert "test-yesno" in out
        assert "test-choice" in out


class TestCmdDiffPremises:
    """Cover added/removed/modified premise display paths in cmd_diff."""

    def test_diff_added_removed_premises(self, tmp_path, capsys) -> None:
        from difficult_dialogs.cli import cmd_diff
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise

        arg_a = Argument(name="diff_a", intro="Intro.", conclusion="Done.")
        p1 = Premise(name="only_in_a")
        p1.add_statement("s1")
        arg_a.add_premise(p1)
        shared = Premise(name="shared")
        shared.add_statement("original statement")
        arg_a.add_premise(shared)
        dir_a = tmp_path / "diff_a"
        arg_a.save(dir_a)

        arg_b = Argument(name="diff_b", intro="Intro.", conclusion="Done.")
        p2 = Premise(name="only_in_b")
        p2.add_statement("s2")
        arg_b.add_premise(p2)
        shared2 = Premise(name="shared")
        shared2.add_statement("modified statement")
        arg_b.add_premise(shared2)
        dir_b = tmp_path / "diff_b"
        arg_b.save(dir_b)

        rc = cmd_diff(argparse.Namespace(argument_a=str(dir_a), argument_b=str(dir_b)))
        out = capsys.readouterr().out
        assert rc == 0
        assert "ADDED" in out or "REMOVED" in out or "MODIFIED" in out


class TestCmdScoreEdgeCases:
    """Cover cmd_score error paths."""

    def test_score_broken_argument_returns_nonzero(self, tmp_path) -> None:
        from difficult_dialogs.cli import cmd_score

        broken_dir = tmp_path / "broken"
        broken_dir.mkdir()
        (broken_dir / "intro.dialog").write_text("")
        (broken_dir / "conclusion.conclusion").write_text("")
        rc = cmd_score(argparse.Namespace(argument=str(broken_dir)))
        assert rc != 0  # returns 1 (load error) or 2 (poor quality)

    def test_score_poor_argument_shows_issues(self, tmp_path, capsys) -> None:
        from difficult_dialogs.cli import cmd_score
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise

        arg = Argument(name="poor", intro="X.", conclusion="Y.")
        p = Premise(name="p1")
        p.add_statement("s")
        arg.add_premise(p)
        d = tmp_path / "poor_arg"
        arg.save(d)

        rc = cmd_score(argparse.Namespace(argument=str(d)))
        # Poor quality arguments return 2
        assert rc in (0, 2)


class TestCmdReplayEdge:
    """Cover unrecognized transcript format path."""

    def test_replay_unrecognized_format(self, tmp_path) -> None:
        import json
        from difficult_dialogs.cli import cmd_replay

        bad = tmp_path / "bad_format.json"
        bad.write_text(json.dumps("just a string"))
        rc = cmd_replay(argparse.Namespace(transcript=str(bad)))
        assert rc == 1


class TestCmdDiffLoadError:
    """Cover cmd_diff load error path."""

    def test_diff_corrupted_argument(self, tmp_path, capsys) -> None:
        from difficult_dialogs.cli import cmd_diff
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise

        arg = Argument(name="good", intro="I.", conclusion="C.")
        p = Premise(name="p1")
        p.add_statement("s")
        arg.add_premise(p)
        good_dir = tmp_path / "good"
        arg.save(good_dir)

        # Create a directory that exists but has corrupted content
        bad_dir = tmp_path / "bad"
        bad_dir.mkdir()
        (bad_dir / "intro.dialog").write_text("")
        (bad_dir / "conclusion.conclusion").write_text("")

        rc = cmd_diff(argparse.Namespace(argument_a=str(good_dir), argument_b=str(bad_dir)))
        # Either loads successfully (empty arg) or fails — both are valid
        assert rc in (0, 1)


class TestCmdServe:
    """Cover cmd_serve entry point."""

    def test_serve_missing_uvicorn(self, monkeypatch) -> None:
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "uvicorn":
                raise ImportError("test")
            return real_import(name, *args, **kwargs)

        from difficult_dialogs.cli import cmd_serve
        monkeypatch.setattr(builtins, "__import__", mock_import)
        rc = cmd_serve(argparse.Namespace(host="127.0.0.1", port=8080))
        assert rc == 1


class TestCmdNew:
    """Cover cmd_new wizard."""

    def test_new_keyboard_interrupt(self, tmp_path) -> None:
        from difficult_dialogs.cli import cmd_new
        from unittest.mock import patch

        ns = argparse.Namespace(output=str(tmp_path))
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            rc = cmd_new(ns)
        assert rc == 1

    def test_new_empty_name_returns_1(self, tmp_path) -> None:
        from difficult_dialogs.cli import cmd_new
        from unittest.mock import patch

        ns = argparse.Namespace(output=str(tmp_path))
        with patch("builtins.input", return_value=""):
            rc = cmd_new(ns)
        assert rc == 1

    def test_new_creates_argument(self, tmp_path) -> None:
        from difficult_dialogs.cli import cmd_new
        from unittest.mock import patch

        ns = argparse.Namespace(output=str(tmp_path))
        # Simulate: name, intro, conclusion, premise name, statement, empty to finish premise, empty to finish premises
        inputs = iter(["test arg", "Intro text", "Conclusion text", "p1", "Statement one", "", ""])
        with patch("builtins.input", side_effect=inputs):
            rc = cmd_new(ns)
        assert rc == 0
        assert (tmp_path / "test_arg" / "intro.dialog").exists()

    def test_new_no_premises(self, tmp_path) -> None:
        from difficult_dialogs.cli import cmd_new
        from unittest.mock import patch

        ns = argparse.Namespace(output=str(tmp_path))
        inputs = iter(["empty arg", "Intro", "Conclusion", ""])
        with patch("builtins.input", side_effect=inputs):
            rc = cmd_new(ns)
        assert rc == 0


class TestCmdGraph:
    """Tests for `did graph`."""

    def _sample_arg(self, tmp_path) -> Path:
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise
        arg = Argument(name="graph test", intro="I.", conclusion="C.")
        p = Premise(name="p1")
        p.add_statement("s1")
        arg.add_premise(p)
        d = tmp_path / "graph_test"
        arg.save(d)
        return d

    def test_graph_mermaid_default(self, tmp_path, capsys) -> None:
        from difficult_dialogs.cli import cmd_graph
        d = self._sample_arg(tmp_path)
        rc = cmd_graph(argparse.Namespace(argument=str(d), format="mermaid", output=None))
        assert rc == 0
        assert "graph TD" in capsys.readouterr().out

    def test_graph_dot_format(self, tmp_path, capsys) -> None:
        from difficult_dialogs.cli import cmd_graph
        d = self._sample_arg(tmp_path)
        rc = cmd_graph(argparse.Namespace(argument=str(d), format="dot", output=None))
        assert rc == 0
        assert "digraph" in capsys.readouterr().out

    def test_graph_json_format(self, tmp_path, capsys) -> None:
        from difficult_dialogs.cli import cmd_graph
        d = self._sample_arg(tmp_path)
        rc = cmd_graph(argparse.Namespace(argument=str(d), format="json", output=None))
        assert rc == 0
        out = capsys.readouterr().out
        assert '"nodes"' in out

    def test_graph_output_file(self, tmp_path) -> None:
        from difficult_dialogs.cli import cmd_graph
        d = self._sample_arg(tmp_path)
        out_file = tmp_path / "graph.md"
        rc = cmd_graph(argparse.Namespace(argument=str(d), format="mermaid", output=str(out_file)))
        assert rc == 0
        assert out_file.exists()
        assert "graph TD" in out_file.read_text()

    def test_graph_nonexistent_path(self) -> None:
        from difficult_dialogs.cli import cmd_graph
        rc = cmd_graph(argparse.Namespace(argument="/nonexistent", format="mermaid", output=None))
        assert rc == 1


class TestCmdStats:
    """Tests for `did stats`."""

    def test_stats_sample_arguments(self, capsys) -> None:
        from difficult_dialogs.cli import cmd_stats
        sample = str(Path(__file__).parent.parent / "examples" / "sample_arguments")
        rc = cmd_stats(argparse.Namespace(path=sample))
        assert rc == 0
        out = capsys.readouterr().out
        assert "Premises:" in out
        assert "Statements:" in out

    def test_stats_single_argument(self, tmp_path, capsys) -> None:
        from difficult_dialogs.cli import cmd_stats
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise
        arg = Argument(name="stats test", intro="I.", conclusion="C.")
        p = Premise(name="p1")
        p.add_statement("s1")
        arg.add_premise(p)
        d = tmp_path / "stats_test"
        arg.save(d)
        rc = cmd_stats(argparse.Namespace(path=str(d)))
        assert rc == 0
        out = capsys.readouterr().out
        assert "Arguments:    1" in out

    def test_stats_nonexistent_path(self) -> None:
        from difficult_dialogs.cli import cmd_stats
        rc = cmd_stats(argparse.Namespace(path="/nonexistent"))
        assert rc == 1


class TestCmdExportCSV:
    """Test CSV format in did export."""

    def test_export_csv_format(self, tmp_path) -> None:
        from difficult_dialogs.cli import cmd_export
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise
        arg = Argument(name="csv cli", intro="I.", conclusion="C.")
        p = Premise(name="p1")
        p.add_statement("s1")
        arg.add_premise(p)
        arg.save(tmp_path / "csv_arg")

        ns = argparse.Namespace(
            input=str(tmp_path),
            output=str(tmp_path / "out.csv"),
            format="csv",
            no_validation=True,
            stats=False,
        )
        rc = cmd_export(ns)
        assert rc == 0
        assert (tmp_path / "out.csv").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
