"""
A statement is the lowest level of a dialog, it is a text sentence that may be True or False

```python
from difficult_dialogs.statements import Statement

s = Statement("i like pizza")
assert str(s) == "i like pizza"
assert s.text == "i like pizza"

assert bool(s) == True
s.disagree()
assert bool(s) == False
s.agree()
assert bool(s) == True
```
"""
from typing import Any


class Statement:
    """A text sentence that may be True or False."""

    def __init__(self, text: str, is_true: bool = True) -> None:
        """
        Args:
            text: the text for this statement.
            is_true: initial truth value.
        """
        self.text: str = str(text)
        self._true: bool = is_true

    def from_json(self, json_dict: dict[str, Any]) -> None:
        """Set properties from a JSON dict.

        Args:
            json_dict: mapping with keys ``text`` and ``is_true``.
        """
        self.text = json_dict.get("text", "")
        self._true = json_dict.get("is_true", True)

    @property
    def as_json(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation."""
        return {"text": self.text, "is_true": self.is_true}

    @property
    def is_true(self) -> bool:
        """Statements are true by default, until user disagrees."""
        return self._true

    def agree(self) -> None:
        """Set statement to True."""
        self._true = True

    def disagree(self) -> None:
        """Set statement to False."""
        self._true = False

    def __str__(self) -> str:
        """Return statement text."""
        return self.text

    def __bool__(self) -> bool:
        """Return statement truth value."""
        return self.is_true
