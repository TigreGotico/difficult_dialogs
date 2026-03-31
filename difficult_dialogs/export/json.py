"""JSON serialization for difficult_dialogs arguments."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from difficult_dialogs.arguments import Argument


class ArgumentEncoder(json.JSONEncoder):
    """Custom JSON encoder for Argument objects."""

    def default(self, obj: Any) -> Any:
        """Convert argument to serializable format."""
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.statements import Statement
        from difficult_dialogs.premises import Premise

        if isinstance(obj, Argument):
            return {
                "name": obj.name,
                "intro": obj.intro,
                "conclusion": obj.conclusion,
                "premises": [self.default(p) for p in obj.premises],
                "is_true": obj.is_true,
            }
        elif isinstance(obj, Premise):
            return {
                "name": obj.name,
                "description": obj.description,
                "statements": [self.default(s) for s in obj.statements],
                "support": obj.support,
                "sources": obj.sources,
                "what": obj.what,
                "why": obj.why,
                "how": obj.how,
                "when": obj.when,
                "where": obj.where,
            }
        elif isinstance(obj, Statement):
            return {
                "text": obj.text,
                "agreed": obj.agreed,
            }

        return super().default(obj)


def export_to_json(argument: Argument, output_path: Path | str) -> Path:
    """Export a single argument to JSON file.

    Args:
        argument: Argument to export.
        output_path: Path to output JSON file.

    Returns:
        Path to created file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = ArgumentEncoder().default(argument)
    data["_export_info"] = {
        "format": "difficult_dialogs_json",
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return output_path


def export_library_to_json(
    arguments_dir: Path | str,
    output_path: Path | str,
    include_validation: bool = True,
) -> Path:
    """Export entire argument library to JSON bundle.

    Args:
        arguments_dir: Directory containing arguments.
        output_path: Path to output JSON bundle.
        include_validation: Include validation scores.

    Returns:
        Path to created file.
    """
    from difficult_dialogs.arguments import Argument
    from difficult_dialogs.validators import validate_argument

    arguments_dir = Path(arguments_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    arguments = []
    validation_results = []

    for intro_file in arguments_dir.rglob("intro.dialog"):
        arg_dir = intro_file.parent
        try:
            arg = Argument().load(arg_dir)
            arguments.append(arg)

            if include_validation:
                val_result = validate_argument(arg)
                validation_results.append({
                    "name": arg.name,
                    "score": val_result.score,
                    "passed": val_result.passed,
                    "issues_count": len(val_result.issues),
                })
        except Exception as e:
            print(f"Warning: Failed to load {arg_dir}: {e}")

    bundle: dict[str, Any] = {
        "_export_info": {
            "format": "difficult_dialogs_library_bundle",
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "total_arguments": len(arguments),
        },
        "arguments": [ArgumentEncoder().default(arg) for arg in arguments],
    }

    if include_validation:
        bundle["validation_summary"] = {
            "results": validation_results,
            "average_score": (
                sum(r["score"] for r in validation_results) / len(validation_results)
                if validation_results else 0
            ),
            "pass_rate": (
                sum(1 for r in validation_results if r["passed"]) / len(validation_results)
                if validation_results else 0
            ),
        }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2, ensure_ascii=False)

    return output_path


def import_from_json(json_path: Path | str) -> Any:
    """Import argument from JSON file.

    Args:
        json_path: Path to JSON file.

    Returns:
        Argument object or list of arguments (for bundles).
    """
    from difficult_dialogs.arguments import Argument

    json_path = Path(json_path)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "_export_info" in data and data["_export_info"].get("format") == "difficult_dialogs_library_bundle":
        return [Argument.from_dict(arg_data) for arg_data in data["arguments"]]

    return Argument.from_dict(data)
