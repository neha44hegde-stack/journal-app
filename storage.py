"""
Storage layer for the journal app. Storage is an ABC so backends are swappable.
"""
from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from models import JournalEntry
from logging_config import get_logger

logger = get_logger(__name__)


class Storage(ABC):
    @abstractmethod
    def add_entry(self, entry: JournalEntry) -> JournalEntry: ...

    @abstractmethod
    def get_all(self) -> list[JournalEntry]: ...

    @abstractmethod
    def get_by_id(self, entry_id: int) -> Optional[JournalEntry]: ...

    @abstractmethod
    def update_mood_score(self, entry_id: int, mood_score: float) -> None: ...

    @abstractmethod
    def update_entry_text(self, entry_id: int, text: str) -> bool: ...

    @abstractmethod
    def delete_entry(self, entry_id: int) -> bool: ...

    @abstractmethod
    def search(self, query: str) -> list[JournalEntry]: ...


class SQLiteStorage(Storage):
    def __init__(self, db_path: str | Path = "journal.db"):
        self.db_path = str(db_path)
        self._init_db()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    mood_score REAL,
                    tags TEXT DEFAULT '',
                    emotions TEXT DEFAULT '{}'
                )
                """
            )
            existing_cols = [row[1] for row in conn.execute("PRAGMA table_info(entries)").fetchall()]
            if "emotions" not in existing_cols:
                conn.execute("ALTER TABLE entries ADD COLUMN emotions TEXT DEFAULT '{}'")

            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts
                USING fts5(text, content='entries', content_rowid='id')
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
                    INSERT INTO entries_fts(rowid, text) VALUES (new.id, new.text);
                END
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
                    INSERT INTO entries_fts(entries_fts, rowid, text) VALUES ('delete', old.id, old.text);
                END
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
                    INSERT INTO entries_fts(entries_fts, rowid, text) VALUES ('delete', old.id, old.text);
                    INSERT INTO entries_fts(rowid, text) VALUES (new.id, new.text);
                END
                """
            )

    def add_entry(self, entry: JournalEntry) -> JournalEntry:
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO entries (text, timestamp, mood_score, tags, emotions) VALUES (?, ?, ?, ?, ?)",
                (
                    entry.text,
                    entry.timestamp.isoformat(),
                    entry.mood_score,
                    ",".join(entry.tags),
                    __import__("json").dumps(entry.emotions),
                ),
            )
            entry.id = cursor.lastrowid
        logger.info("Entry added (id=%s, chars=%d)", entry.id, len(entry.text))
        return entry

    def get_all(self) -> list[JournalEntry]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, text, timestamp, mood_score, tags, emotions FROM entries ORDER BY timestamp DESC"
            ).fetchall()
        return [JournalEntry.from_row(row) for row in rows]

    def get_by_id(self, entry_id: int) -> Optional[JournalEntry]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, text, timestamp, mood_score, tags, emotions FROM entries WHERE id = ?",
                (entry_id,),
            ).fetchone()
        return JournalEntry.from_row(row) if row else None

    def update_mood_score(self, entry_id: int, mood_score: float) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE entries SET mood_score = ? WHERE id = ?",
                (mood_score, entry_id),
            )

    def update_entry_text(self, entry_id: int, text: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE entries SET text = ? WHERE id = ?",
                (text, entry_id),
            )
        updated = cursor.rowcount > 0
        logger.info("Entry text updated (id=%s, success=%s)", entry_id, updated)
        return updated

    def delete_entry(self, entry_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        deleted = cursor.rowcount > 0
        logger.info("Delete requested (id=%s, success=%s)", entry_id, deleted)
        return deleted

    def search(self, query: str) -> list[JournalEntry]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT e.id, e.text, e.timestamp, e.mood_score, e.tags, e.emotions
                FROM entries e
                JOIN entries_fts f ON e.id = f.rowid
                WHERE entries_fts MATCH ?
                ORDER BY e.timestamp DESC
                """,
                (query,),
            ).fetchall()
        return [JournalEntry.from_row(row) for row in rows]

    def iter_all(self) -> Iterator[JournalEntry]:
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT id, text, timestamp, mood_score, tags, emotions FROM entries ORDER BY timestamp"
            )
            for row in cursor:
                yield JournalEntry.from_row(row)