"""
Wraps SQLiteStorage to transparently encrypt entry text at rest.
"""
from __future__ import annotations

from typing import Optional

from models import JournalEntry
from security import JournalCipher
from storage import SQLiteStorage


class EncryptedJournalStorage:
    def __init__(self, storage: SQLiteStorage, cipher: JournalCipher):
        self._storage = storage
        self._cipher = cipher

    def add_entry(self, entry: JournalEntry) -> JournalEntry:
        encrypted_entry = JournalEntry(
            text=self._cipher.encrypt(entry.text),
            timestamp=entry.timestamp,
            mood_score=entry.mood_score,
            tags=entry.tags,
            emotions=entry.emotions,
        )
        saved = self._storage.add_entry(encrypted_entry)
        entry.id = saved.id
        return entry

    def _decrypt(self, entry: JournalEntry) -> JournalEntry:
        entry.text = self._cipher.decrypt(entry.text)
        return entry

    def get_all(self) -> list[JournalEntry]:
        return [self._decrypt(e) for e in self._storage.get_all()]

    def get_by_id(self, entry_id: int) -> Optional[JournalEntry]:
        entry = self._storage.get_by_id(entry_id)
        return self._decrypt(entry) if entry else None

    def update_mood_score(self, entry_id: int, mood_score: float) -> None:
        self._storage.update_mood_score(entry_id, mood_score)

    def update_entry_text(self, entry_id: int, text: str) -> bool:
        return self._storage.update_entry_text(entry_id, self._cipher.encrypt(text))

    def delete_entry(self, entry_id: int) -> bool:
        return self._storage.delete_entry(entry_id)

    def search(self, query: str) -> list[JournalEntry]:
        query_lower = query.lower()
        matches = []
        for entry in self.get_all():
            if query_lower in entry.text.lower():
                matches.append(entry)
        return matches