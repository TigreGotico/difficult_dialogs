"""Markdown export for difficult_dialogs arguments."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from difficult_dialogs.arguments import Argument


def export_to_markdown(argument: Argument, output_path: Path | str | None = None) -> str:
    """Export an argument as a human-readable Markdown document.

    Args:
        argument: Argument to export.
        output_path: Optional path to write the Markdown file.
                     If None, returns the string without writing.

    Returns:
        Markdown string.
    """
    lines: list[str] = []

    lines.append(f"# {argument.name.title()}")
    lines.append("")

    if argument.intro:
        lines.append(argument.intro)
        lines.append("")

    if argument.premises:
        lines.append("## Premises")
        lines.append("")
        for i, premise in enumerate(argument.premises, 1):
            lines.append(f"### {i}. {premise.description}")
            lines.append("")

            if premise.statements:
                for stmt in premise.statements:
                    lines.append(f"- {stmt.text}")
                lines.append("")

            for label, items in (
                ("What", premise.what),
                ("Why", premise.why),
                ("How", premise.how),
                ("When", premise.when),
                ("Where", premise.where),
            ):
                if items:
                    lines.append(f"**{label}:** {items[0]}")
                    for item in items[1:]:
                        lines.append(f"  {item}")
                    lines.append("")

            if premise.support:
                lines.append("**Supporting arguments:**")
                for text in premise.support:
                    lines.append(f"- {text}")
                lines.append("")

            if premise.sources:
                lines.append("**Sources:**")
                for url in premise.sources:
                    lines.append(f"- {url}")
                lines.append("")

    if argument.conclusion:
        lines.append("## Conclusion")
        lines.append("")
        lines.append(argument.conclusion)
        lines.append("")

    content = "\n".join(lines)

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

    return content
