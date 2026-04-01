"""ArgumentLibrary — index and search a collection of on-disk arguments.

Scans a root directory tree (category/argument_name/ layout as used in
``examples/sample_arguments/``), builds a lightweight in-memory index, and
exposes keyword search across names, intros, conclusions, and premise
statements — all without touching an LLM or a database.

Usage::

    from difficult_dialogs.library import ArgumentLibrary

    lib = ArgumentLibrary("examples/sample_arguments")
    lib.scan()                                   # index once

    results = lib.search("climate change")       # keyword search
    for r in results:
        print(r.argument.name, r.score)

    categories = lib.categories()               # ["health", "science", …]
    args = lib.by_category("health")            # list[Argument]
    arg   = lib.get("regular exercise improves mental health")
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from difficult_dialogs.arguments import Argument


@dataclass
class SearchResult:
    """A ranked search result."""
    argument: Argument
    category: str
    score: float          # higher = more relevant
    matched_fields: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"SearchResult(name={self.argument.name!r}, "
            f"category={self.category!r}, score={self.score:.2f})"
        )


@dataclass
class _IndexEntry:
    argument: Argument
    category: str
    searchable: str   # lowercased concatenation of all text fields


class ArgumentLibrary:
    """Scans and indexes a directory tree of arguments for offline search.

    Directory layout expected::

        root/
        ├── category_a/
        │   ├── argument_one/
        │   └── argument_two/
        └── category_b/
            └── argument_three/

    A flat layout (no category subdirectories) is also supported — all
    arguments are assigned to the category ``"uncategorised"``.

    Args:
        root: Path to the directory tree to scan.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self._index: list[_IndexEntry] = []
        self._scanned = False

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def scan(self, *, reload: bool = False) -> ArgumentLibrary:
        """Walk *root* and index all valid argument directories.

        Args:
            reload: Force re-scan even if already scanned.

        Returns:
            Self for method chaining.

        Raises:
            FileNotFoundError: If *root* does not exist.
        """
        if self._scanned and not reload:
            return self
        if not self.root.exists():
            raise FileNotFoundError(f"Library root not found: {self.root}")

        self._index.clear()

        for item in sorted(self.root.iterdir()):
            if not item.is_dir() or item.name.startswith("."):
                continue

            # Determine if this is a category dir or a bare argument dir
            if (item / "intro.dialog").exists():
                # Flat layout — item is an argument, no category
                self._index_argument(item, category="uncategorised")
            else:
                # Category layout — iterate children
                for arg_dir in sorted(item.iterdir()):
                    if arg_dir.is_dir() and (arg_dir / "intro.dialog").exists():
                        self._index_argument(arg_dir, category=item.name)

        self._scanned = True
        return self

    def _index_argument(self, path: Path, category: str) -> None:
        try:
            arg = Argument.from_directory(path)
        except Exception:
            return

        parts = [arg.name, arg.intro, arg.conclusion]
        for premise in arg.premises:
            for stmt in premise.statements:
                parts.append(stmt.text)
            parts.extend(premise.support)
            parts.extend(premise.what)
            parts.extend(premise.why)
            parts.extend(premise.how)

        searchable = " ".join(parts).lower()
        self._index.append(_IndexEntry(argument=arg, category=category, searchable=searchable))

    # ------------------------------------------------------------------
    # Query interface
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        *,
        category: str | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Search the index for arguments matching *query*.

        Scoring is token-based: each query word that appears in the
        searchable text adds 1 to the score.  Results are sorted by
        descending score; ties preserve scan order.

        Args:
            query: Space-separated keywords to search for.
            category: Restrict results to this category (optional).
            limit: Maximum number of results to return.

        Returns:
            List of :class:`SearchResult` ordered by relevance.
        """
        if not self._scanned:
            self.scan()

        tokens = query.lower().split()
        if not tokens:
            return []

        results: list[SearchResult] = []
        for entry in self._index:
            if category and entry.category.lower() != category.lower():
                continue
            matched = [t for t in tokens if t in entry.searchable]
            if not matched:
                continue
            score = len(matched) / len(tokens)
            results.append(SearchResult(
                argument=entry.argument,
                category=entry.category,
                score=score,
                matched_fields=matched,
            ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def categories(self) -> list[str]:
        """Return sorted list of unique category names in the index.

        Returns:
            Sorted list of category name strings.
        """
        if not self._scanned:
            self.scan()
        return sorted({e.category for e in self._index})

    def by_category(self, category: str) -> list[Argument]:
        """Return all arguments belonging to *category*.

        Args:
            category: Category name (case-insensitive).

        Returns:
            List of :class:`Argument` instances.
        """
        if not self._scanned:
            self.scan()
        return [
            e.argument for e in self._index
            if e.category.lower() == category.lower()
        ]

    def get(self, name: str) -> Argument | None:
        """Look up an argument by exact name (case-insensitive).

        Args:
            name: Argument name, e.g. ``"regular exercise improves mental health"``.

        Returns:
            The :class:`Argument` if found, else ``None``.
        """
        if not self._scanned:
            self.scan()
        name_lower = name.lower()
        for entry in self._index:
            if entry.argument.name.lower() == name_lower:
                return entry.argument
        return None

    def all_arguments(self) -> list[Argument]:
        """Return all indexed arguments in scan order.

        Returns:
            List of all :class:`Argument` instances.
        """
        if not self._scanned:
            self.scan()
        return [e.argument for e in self._index]

    def __len__(self) -> int:
        if not self._scanned:
            self.scan()
        return len(self._index)

    def watch(
        self,
        callback: "Callable[[ArgumentLibrary], None]",
    ) -> "threading.Thread":
        """Watch *root* for filesystem changes and re-scan automatically.

        Uses the ``watchdog`` package (inotify/FSEvents/ReadDirectoryChanges)
        to detect ``.dialog`` and ``.premise`` file changes.  Calls *callback*
        with ``self`` after every re-scan.  Runs in a background daemon thread.

        Requires the ``watchdog`` optional dependency::

            pip install "difficult_dialogs[watch]"

        Args:
            callback: Callable invoked after each re-scan.  Receives this
                :class:`ArgumentLibrary` instance as its only argument.

        Returns:
            The background watchdog :class:`Observer` (already started).

        Raises:
            ImportError: If the ``watchdog`` package is not installed.

        Example::

            lib = ArgumentLibrary("arguments/").scan()

            def on_change(updated_lib):
                print(f"Reloaded — {len(updated_lib)} arguments indexed")

            thread = lib.watch(on_change)
            # thread is a daemon thread; it will stop when your process exits
        """
        try:
            from watchdog.observers import Observer  # type: ignore[import]
            from watchdog.events import FileSystemEventHandler  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "ArgumentLibrary.watch() requires the 'watchdog' package. "
                "Install it with:  pip install \"difficult_dialogs[watch]\""
            ) from exc

        lib_ref = self

        class _Handler(FileSystemEventHandler):
            def on_any_event(self, event) -> None:  # type: ignore[override]
                if event.is_directory:
                    return
                lib_ref.scan(reload=True)
                callback(lib_ref)

        observer = Observer()
        observer.schedule(_Handler(), str(self.root), recursive=True)
        observer.daemon = True  # type: ignore[attr-defined]
        observer.start()
        return observer  # type: ignore[return-value]

    def __repr__(self) -> str:
        n = len(self._index) if self._scanned else "?"
        return f"ArgumentLibrary(root={self.root!r}, indexed={n})"
