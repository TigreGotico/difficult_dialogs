"""Tests for difficult_dialogs.export.csv."""
import csv
from pathlib import Path

from difficult_dialogs.arguments import Argument
from difficult_dialogs.builder import ArgumentBuilder
from difficult_dialogs.export.csv import export_to_csv, export_library_to_csv
from difficult_dialogs.premises import Premise


def _sample_arg():
    return (
        ArgumentBuilder("csv_test")
        .intro("Intro.")
        .conclusion("Done.")
        .premise("p1").statement("Claim one.").statement("Claim two.").support("Evidence.").done()
        .premise("p2").statement("Claim three.").on_agree("p1").done()
        .build()
    )


class TestExportToCSV:
    def test_creates_file(self, tmp_path: Path) -> None:
        out = tmp_path / "test.csv"
        export_to_csv(_sample_arg(), out)
        assert out.exists()

    def test_header_row(self, tmp_path: Path) -> None:
        out = tmp_path / "test.csv"
        export_to_csv(_sample_arg(), out)
        with open(out) as f:
            reader = csv.reader(f)
            header = next(reader)
        assert "argument_name" in header
        assert "premise_name" in header
        assert "statement_text" in header

    def test_row_count(self, tmp_path: Path) -> None:
        out = tmp_path / "test.csv"
        export_to_csv(_sample_arg(), out)
        with open(out) as f:
            rows = list(csv.reader(f))
        # header + 3 statements (2 in p1, 1 in p2)
        assert len(rows) == 4

    def test_support_count(self, tmp_path: Path) -> None:
        out = tmp_path / "test.csv"
        export_to_csv(_sample_arg(), out)
        with open(out) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        p1_rows = [r for r in rows if r["premise_name"] == "p1"]
        assert all(r["support_count"] == "1" for r in p1_rows)

    def test_on_agree_column(self, tmp_path: Path) -> None:
        out = tmp_path / "test.csv"
        export_to_csv(_sample_arg(), out)
        with open(out) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        p2_row = next(r for r in rows if r["premise_name"] == "p2")
        assert p2_row["on_agree"] == "p1"

    def test_returns_path(self, tmp_path: Path) -> None:
        out = tmp_path / "test.csv"
        result = export_to_csv(_sample_arg(), out)
        assert result == out


class TestExportLibraryToCSV:
    def _make_library(self, tmp_path: Path) -> Path:
        root = tmp_path / "library"
        cat = root / "science"
        cat.mkdir(parents=True)
        arg = _sample_arg()
        arg.save(cat / "csv_test")
        return root

    def test_creates_file(self, tmp_path: Path) -> None:
        root = self._make_library(tmp_path)
        out = tmp_path / "library.csv"
        export_library_to_csv(root, out)
        assert out.exists()

    def test_has_category(self, tmp_path: Path) -> None:
        root = self._make_library(tmp_path)
        out = tmp_path / "library.csv"
        export_library_to_csv(root, out)
        with open(out) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert any(r["category"] == "science" for r in rows)

    def test_returns_path(self, tmp_path: Path) -> None:
        root = self._make_library(tmp_path)
        out = tmp_path / "library.csv"
        result = export_library_to_csv(root, out)
        assert result == out
