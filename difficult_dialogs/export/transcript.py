"""Transcript export utilities.

Converts a completed (or in-progress) :class:`BasePolicy` session transcript
into human-readable Markdown or a plain JSON list.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from difficult_dialogs.policy import BasePolicy, PolicyState


def export_transcript_to_markdown(
    policy: BasePolicy | PolicyState,
    output_path: str | Path | None = None,
    *,
    title: str | None = None,
) -> str:
    """Render the session transcript as a Markdown document.

    Accepts either a :class:`BasePolicy` instance (reads ``policy.state``) or
    a bare :class:`PolicyState` so callers can export a restored/deserialised
    state without a live policy object.

    Args:
        policy: A ``BasePolicy`` instance or a ``PolicyState`` object.
        output_path: Optional file path to write the Markdown string into.
        title: Optional document title.  Defaults to the argument name when
               a ``BasePolicy`` is provided, otherwise ``"Session Transcript"``.

    Returns:
        The rendered Markdown string.
    """
    from difficult_dialogs.policy import BasePolicy as _BasePolicy, PolicyState as _PolicyState

    if isinstance(policy, _BasePolicy):
        state = policy.state
        default_title = policy.argument.name.replace("_", " ").title()
    elif isinstance(policy, _PolicyState):
        state = policy
        default_title = "Session Transcript"
    else:
        raise TypeError(f"Expected BasePolicy or PolicyState, got {type(policy)!r}")

    doc_title = title or default_title
    lines: list[str] = [f"# {doc_title} — Transcript", ""]

    if not state.transcript:
        lines.append("*(no turns recorded)*")
    else:
        from datetime import datetime, timezone
        for entry in state.transcript:
            ts = ""
            if entry.timestamp is not None:
                ts = f" *({datetime.fromtimestamp(entry.timestamp, tz=timezone.utc).isoformat()})*"
            if entry.role == "bot":
                lines.append(f"**Bot:** {entry.text}{ts}")
            else:
                lines.append(f"**User:** {entry.text}{ts}")
            lines.append("")

    lines.append("---")
    lines.append(f"*Finished: {'yes' if state.finished else 'no'}*")
    if state.current_premise:
        lines.append(f"*Last premise: {state.current_premise}*")

    result = "\n".join(lines)

    if output_path is not None:
        Path(output_path).write_text(result, encoding="utf-8")

    return result


def export_transcript_to_json(
    policy: BasePolicy | PolicyState,
    output_path: str | Path | None = None,
) -> list[dict[str, str]]:
    """Export the session transcript as a JSON-serialisable list.

    Each element is ``{"role": "bot"|"user", "text": "…"}``.

    Args:
        policy: A ``BasePolicy`` instance or a ``PolicyState`` object.
        output_path: Optional file path to write pretty-printed JSON into.

    Returns:
        List of transcript entry dicts.
    """
    from difficult_dialogs.policy import BasePolicy as _BasePolicy, PolicyState as _PolicyState

    if isinstance(policy, _BasePolicy):
        state = policy.state
    elif isinstance(policy, _PolicyState):
        state = policy
    else:
        raise TypeError(f"Expected BasePolicy or PolicyState, got {type(policy)!r}")

    entries = [e.to_dict() for e in state.transcript]

    if output_path is not None:
        Path(output_path).write_text(json.dumps(entries, indent=2, ensure_ascii=False))

    return entries
