"""
Data models for the journal app.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class JournalEntry:
    text: str
    timestamp: datetime = field(default_factory=datetime.now)
    mood_score: Optional[float] = None
    tags: list[str] = field(default_factory=list)
    emotions: dict[str, float] = field(default_factory=dict)
    id: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "timestamp": self.timestamp.isoformat(),
            "mood_score": self.mood_score,
            "tags": ",".join(self.tags),
            "emotions": json.dumps(self.emotions),
        }

    @classmethod
    def from_row(cls, row: tuple) -> "JournalEntry":
        entry_id, text, timestamp, mood_score, tags, emotions_json = row
        return cls(
            id=entry_id,
            text=text,
            timestamp=datetime.fromisoformat(timestamp),
            mood_score=mood_score,
            tags=tags.split(",") if tags else [],
            emotions=json.loads(emotions_json) if emotions_json else {},
        )

    def preview(self, length: int = 60) -> str:
        flat = self.text.replace("\n", " ").strip()
        return flat if len(flat) <= length else flat[: length - 1] + "…"