"""SQLite database export for difficult_dialogs argument libraries."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from difficult_dialogs.arguments import Argument


class LibraryDatabase:
    """SQLite database for argument libraries."""

    def __init__(self, db_path: Path | str) -> None:
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        """Create database schema."""
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS arguments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                intro TEXT NOT NULL,
                conclusion TEXT NOT NULL,
                is_true BOOLEAN DEFAULT 1,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS premises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                argument_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                position INTEGER NOT NULL,
                FOREIGN KEY (argument_id) REFERENCES arguments(id) ON DELETE CASCADE,
                UNIQUE(argument_id, name)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                premise_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                agreed BOOLEAN DEFAULT 1,
                position INTEGER NOT NULL,
                FOREIGN KEY (premise_id) REFERENCES premises(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                premise_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                FOREIGN KEY (premise_id) REFERENCES premises(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS support (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                premise_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                position INTEGER NOT NULL,
                FOREIGN KEY (premise_id) REFERENCES premises(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS five_ws (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                premise_id INTEGER NOT NULL,
                w_type TEXT NOT NULL,
                text TEXT NOT NULL,
                position INTEGER NOT NULL,
                FOREIGN KEY (premise_id) REFERENCES premises(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                argument_id INTEGER NOT NULL UNIQUE,
                score REAL NOT NULL,
                passed BOOLEAN NOT NULL,
                issues_count INTEGER DEFAULT 0,
                validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (argument_id) REFERENCES arguments(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_five_ws_premise ON five_ws(premise_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_support_premise ON support(premise_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_arguments_category ON arguments(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_premises_argument ON premises(argument_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_statements_premise ON statements(premise_id)")

        self.conn.commit()

    def add_argument(self, argument: Argument, category: str | None = None) -> int:
        """Add argument to database.

        Args:
            argument: Argument to add.
            category: Optional category name.

        Returns:
            Database ID of inserted argument.
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO arguments (name, intro, conclusion, is_true, category)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                intro = excluded.intro,
                conclusion = excluded.conclusion,
                is_true = excluded.is_true,
                category = excluded.category,
                updated_at = CURRENT_TIMESTAMP
        """, (argument.name, argument.intro, argument.conclusion, argument.is_true, category))

        arg_id = cursor.lastrowid if cursor.lastrowid else self._get_argument_id(argument.name)

        cursor.execute("DELETE FROM premises WHERE argument_id = ?", (arg_id,))

        for i, premise in enumerate(argument.premises):
            cursor.execute("""
                INSERT INTO premises (argument_id, name, description, position)
                VALUES (?, ?, ?, ?)
            """, (arg_id, premise.name, premise.description, i))

            premise_id = cursor.lastrowid

            for j, stmt in enumerate(premise.statements):
                cursor.execute("""
                    INSERT INTO statements (premise_id, text, agreed, position)
                    VALUES (?, ?, ?, ?)
                """, (premise_id, stmt.text, stmt.agreed, j))

            for source in premise.sources:
                cursor.execute(
                    "INSERT INTO sources (premise_id, url) VALUES (?, ?)",
                    (premise_id, source),
                )

            for k, text in enumerate(premise.support):
                cursor.execute(
                    "INSERT INTO support (premise_id, text, position) VALUES (?, ?, ?)",
                    (premise_id, text, k),
                )

            for w_type in ("what", "why", "how", "when", "where"):
                for k, text in enumerate(getattr(premise, w_type)):
                    cursor.execute(
                        "INSERT INTO five_ws (premise_id, w_type, text, position) VALUES (?, ?, ?, ?)",
                        (premise_id, w_type, text, k),
                    )

        self.conn.commit()
        return arg_id

    def _get_argument_id(self, name: str) -> int:
        """Get argument ID by name."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM arguments WHERE name = ?", (name,))
        row = cursor.fetchone()
        return row["id"] if row else 0

    def add_validation_result(
        self, argument_name: str, score: float, passed: bool, issues_count: int
    ) -> None:
        """Store validation result for an argument.

        Args:
            argument_name: Name of argument.
            score: Validation score (0.0-1.0).
            passed: Whether validation passed.
            issues_count: Number of validation issues.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO validation (argument_id, score, passed, issues_count)
            SELECT id, ?, ?, ? FROM arguments WHERE name = ?
            ON CONFLICT(argument_id) DO UPDATE SET
                score = excluded.score,
                passed = excluded.passed,
                issues_count = excluded.issues_count,
                validated_at = CURRENT_TIMESTAMP
        """, (score, passed, issues_count, argument_name))
        self.conn.commit()

    def get_argument(self, name: str) -> Any | None:
        """Retrieve argument from database.

        Args:
            name: Argument name.

        Returns:
            Argument object or None.
        """
        from difficult_dialogs.arguments import Argument
        from difficult_dialogs.premises import Premise
        from difficult_dialogs.statements import Statement

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM arguments WHERE name = ?", (name,))
        arg_row = cursor.fetchone()

        if not arg_row:
            return None

        arg = Argument(
            name=arg_row["name"],
            intro=arg_row["intro"],
            conclusion=arg_row["conclusion"],
        )

        cursor.execute("""
            SELECT * FROM premises
            WHERE argument_id = ?
            ORDER BY position
        """, (arg_row["id"],))

        for premise_row in cursor.fetchall():
            premise = Premise(
                name=premise_row["name"],
                description=premise_row["description"] or "",
            )

            cursor.execute("""
                SELECT * FROM statements
                WHERE premise_id = ?
                ORDER BY position
            """, (premise_row["id"],))

            for stmt_row in cursor.fetchall():
                stmt = Statement(text=stmt_row["text"])
                stmt.agreed = bool(stmt_row["agreed"])
                premise.statements.append(stmt)

            cursor.execute(
                "SELECT url FROM sources WHERE premise_id = ? ORDER BY rowid",
                (premise_row["id"],),
            )
            premise.sources = [row["url"] for row in cursor.fetchall()]

            cursor.execute(
                "SELECT text FROM support WHERE premise_id = ? ORDER BY position",
                (premise_row["id"],),
            )
            premise.support = [row["text"] for row in cursor.fetchall()]

            cursor.execute(
                "SELECT w_type, text FROM five_ws WHERE premise_id = ? ORDER BY w_type, position",
                (premise_row["id"],),
            )
            for row in cursor.fetchall():
                adder = getattr(premise, f"add_{row['w_type']}")
                adder(row["text"])

            arg.add_premise(premise)

        return arg

    def list_arguments(self, category: str | None = None) -> list[str]:
        """List all argument names.

        Args:
            category: Optional category filter.

        Returns:
            List of argument names.
        """
        cursor = self.conn.cursor()

        if category:
            cursor.execute(
                "SELECT name FROM arguments WHERE category = ? ORDER BY name",
                (category,),
            )
        else:
            cursor.execute("SELECT name FROM arguments ORDER BY name")

        return [row["name"] for row in cursor.fetchall()]

    def get_statistics(self) -> dict[str, Any]:
        """Get library statistics.

        Returns:
            Dictionary with statistics.
        """
        cursor = self.conn.cursor()

        stats: dict[str, Any] = {}

        cursor.execute("SELECT COUNT(*) FROM arguments")
        stats["total_arguments"] = cursor.fetchone()[0]

        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM arguments
            GROUP BY category
        """)
        stats["by_category"] = {row["category"]: row["count"] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT AVG(score), MIN(score), MAX(score), COUNT(*)
            FROM validation
        """)
        val_row = cursor.fetchone()
        stats["validation"] = {
            "average_score": val_row[0] or 0,
            "min_score": val_row[1] or 0,
            "max_score": val_row[2] or 0,
            "validated_count": val_row[3] or 0,
        }

        return stats

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()


def export_to_sqlite(
    arguments_dir: Path | str,
    db_path: Path | str,
    include_validation: bool = True,
) -> LibraryDatabase:
    """Export entire library to SQLite database.

    Args:
        arguments_dir: Directory containing arguments.
        db_path: Path to SQLite database file.
        include_validation: Include validation results.

    Returns:
        LibraryDatabase instance.
    """
    from difficult_dialogs.arguments import Argument
    from difficult_dialogs.validators import validate_argument

    arguments_dir = Path(arguments_dir)
    db = LibraryDatabase(db_path)

    added = 0
    for intro_file in arguments_dir.rglob("intro.dialog"):
        arg_dir = intro_file.parent
        rel_path = arg_dir.relative_to(arguments_dir)
        category = rel_path.parts[0] if len(rel_path.parts) > 1 else None

        try:
            arg = Argument().load(arg_dir)
            db.add_argument(arg, category)

            if include_validation:
                result = validate_argument(arg)
                db.add_validation_result(arg.name, result.score, result.passed, len(result.issues))

            added += 1
        except Exception as e:
            print(f"Warning: Failed to export {arg_dir}: {e}")

    print(f"Exported {added} arguments to {db_path}")
    return db
