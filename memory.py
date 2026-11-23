import sqlite3
from pathlib import Path


class Memory:
    def __init__(self, db_path: str):
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(db_path)
        self._connection.row_factory = sqlite3.Row
        self._initialize()

    def _initialize(self) -> None:
        with self._connection:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY,
                    fact TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS commands (
                    id INTEGER PRIMARY KEY,
                    command TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def add_message(self, role: str, content: str) -> None:
        with self._connection:
            self._connection.execute(
                "INSERT INTO messages (role, content) VALUES (?, ?)",
                (role, content),
            )

    def recent_messages(self, turns: int) -> list[dict[str, str]]:
        if turns <= 0:
            return []
        rows = self._connection.execute(
            """
            SELECT role, content
            FROM messages
            ORDER BY id DESC
            LIMIT ?
            """,
            (turns * 2,),
        ).fetchall()
        return [
            {"role": row["role"], "content": row["content"]}
            for row in reversed(rows)
        ]

    def add_fact(self, fact: str) -> None:
        with self._connection:
            self._connection.execute(
                "INSERT OR IGNORE INTO facts (fact) VALUES (?)",
                (fact,),
            )

    def all_facts(self) -> list[str]:
        rows = self._connection.execute(
            "SELECT fact FROM facts ORDER BY id"
        ).fetchall()
        return [row["fact"] for row in rows]

    def log_command(self, command: str) -> None:
        with self._connection:
            self._connection.execute(
                "INSERT INTO commands (command) VALUES (?)",
                (command,),
            )

    def close(self) -> None:
        self._connection.close()
