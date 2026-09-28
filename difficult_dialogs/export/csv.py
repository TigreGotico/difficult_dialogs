"""CSV export for difficult_dialogs arguments.

Writes one row per statement in long (denormalized) format, suitable for
direct import into pandas, Excel, or R without reshaping.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from difficult_dialogs.arguments import Argument

_COLUMNS = [
    "argument_name",
    "category",
    "premise_name",
    "statement_text",
    "support_count",
    "source_count",
    "has_choices",
    "on_agree",
    "on_disagree",
]


def _argument_rows(argument: "Argument", category: str = "") -> list[list[str]]:
    """Generate CSV rows for a single argument."""
    rows: list[list[str]] = []
    for premise in argument.premises:
        for stmt in premise.statements:
            rows.append([
                argument.name,
                category,
                premise.name,
                str(stmt),
                str(len(premise.support)),
                str(len(premise.sources)),
                str(bool(premise.choices)),
                premise.on_agree or "",
                premise.on_disagree or "",
            ])
    return rows


def export_to_csv(argument: "Argument", output_path: Path | str) -> Path:
    """Export a single argument to a CSV file.

    One row per statement, columns: argument_name, category, premise_name,
    statement_text, support_count, source_count, has_choices, on_agree,
    on_disagree.

    Args:
        argument: Argument to export.
        output_path: Destination file path.

    Returns:
        Path to the created file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(_COLUMNS)
        writer.writerows(_argument_rows(argument))

    return output_path


def export_library_to_csv(
    arguments_dir: Path | str,
    output_path: Path | str,
) -> Path:
    """Export all arguments in a directory to a single CSV file.

    Scans for ``intro.dialog`` files recursively. The immediate parent
    directory of each argument is used as the category name (or
    ``"uncategorized"`` for flat layouts).

    Args:
        arguments_dir: Root directory to scan.
        output_path: Destination CSV file.

    Returns:
        Path to the created file.
    """
    from difficult_dialogs.arguments import Argument

    arguments_dir = Path(arguments_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    all_rows: list[list[str]] = []

    for intro_file in sorted(arguments_dir.rglob("intro.dialog")):
        arg_dir = intro_file.parent
        rel = arg_dir.relative_to(arguments_dir)
        category = rel.parts[0] if len(rel.parts) > 1 else "uncategorized"

        try:
            arg = Argument.from_directory(arg_dir)
        except Exception:
            continue

        all_rows.extend(_argument_rows(arg, category=category))

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(_COLUMNS)
        writer.writerows(all_rows)

    return output_path
