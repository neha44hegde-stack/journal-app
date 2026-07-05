"""
Generates a real written reflection on recent journal entries using the
Anthropic API, instead of just aggregate stats. Uses only the standard
library (urllib) so no extra package install is required.

Privacy note: only entry text, mood scores, and emotion labels are sent.
The password, salt, and encryption key never leave the machine.
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error

from config import settings
from models import JournalEntry

_API_URL = "https://api.anthropic.com/v1/messages"
_MAX_ENTRIES_SENT = 10


class AIInsightError(Exception):
    """Raised when the AI insight request can't be completed."""


def _build_prompt(entries: list[JournalEntry]) -> str:
    lines = ["Here are my recent journal entries, most recent first:\n"]
    for entry in entries[:_MAX_ENTRIES_SENT]:
        dominant = max(entry.emotions, key=entry.emotions.get) if entry.emotions and max(entry.emotions.values()) > 0 else "neutral"
        lines.append(f"- [{entry.timestamp:%Y-%m-%d}] (mood: {dominant}) {entry.text}")

    lines.append(
        "\nBased only on these entries, write a short (4-6 sentence) reflective "
        "summary. Notice any patterns in what's been on my mind or how I've been "
        "feeling. Be warm and specific, not generic. Do not diagnose me with any "
        "condition. If nothing stands out, say so honestly rather than inventing "
        "a pattern."
    )
    return "\n".join(lines)


def generate_ai_insight(entries: list[JournalEntry]) -> str:
    if not settings.anthropic_api_key:
        raise AIInsightError(
            "No API key set. Set the ANTHROPIC_API_KEY environment variable to enable this feature."
        )
    if not entries:
        raise AIInsightError("No entries yet - write a few first.")

    prompt = _build_prompt(entries)
    payload = json.dumps({
        "model": settings.ai_model,
        "max_tokens": 400,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    request = urllib.request.Request(
        _API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise AIInsightError(f"API request failed ({exc.code}): {body[:200]}") from exc
    except urllib.error.URLError as exc:
        raise AIInsightError(f"Could not reach the API: {exc.reason}") from exc

    try:
        text_blocks = [block["text"] for block in data["content"] if block.get("type") == "text"]
        return "\n".join(text_blocks).strip()
    except (KeyError, TypeError) as exc:
        raise AIInsightError("Unexpected response format from the API.") from exc