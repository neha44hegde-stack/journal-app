"""
Mood scoring per entry + aggregate insights across entries.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter
from datetime import datetime
from typing import Optional

from models import JournalEntry

_POSITIVE_WORDS = {
    "happy", "good", "great", "excited", "grateful", "love", "joy", "proud",
    "calm", "hopeful", "relieved", "confident", "peaceful", "wonderful",
    "excellent", "glad", "fun", "success", "accomplished", "energized",
}
_NEGATIVE_WORDS = {
    "sad", "bad", "angry", "anxious", "stressed", "worried", "tired",
    "frustrated", "upset", "lonely", "hate", "fear", "afraid", "depressed",
    "overwhelmed", "hurt", "disappointed", "exhausted", "failure", "awful",
}


class SentimentAnalyzer(ABC):
    @abstractmethod
    def score(self, text: str) -> float:
        """Return a mood score in [-1.0, 1.0]."""


class LexiconAnalyzer(SentimentAnalyzer):
    def score(self, text: str) -> float:
        words = [w.strip(".,!?;:\"'()").lower() for w in text.split()]
        if not words:
            return 0.0
        pos = sum(1 for w in words if w in _POSITIVE_WORDS)
        neg = sum(1 for w in words if w in _NEGATIVE_WORDS)
        total_hits = pos + neg
        if total_hits == 0:
            return 0.0
        return (pos - neg) / total_hits


class VaderAnalyzer(SentimentAnalyzer):
    def __init__(self):
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        self._analyzer = SentimentIntensityAnalyzer()

    def score(self, text: str) -> float:
        return self._analyzer.polarity_scores(text)["compound"]


def get_default_analyzer() -> SentimentAnalyzer:
    try:
        return VaderAnalyzer()
    except ImportError:
        return LexiconAnalyzer()


def mood_label(score: Optional[float]) -> str:
    if score is None:
        return "unscored"
    if score > 0.3:
        return "positive"
    if score < -0.3:
        return "negative"
    return "neutral"


def average_mood(entries: list[JournalEntry]) -> Optional[float]:
    scored = [e.mood_score for e in entries if e.mood_score is not None]
    return sum(scored) / len(scored) if scored else None


def mood_trend(entries: list[JournalEntry]) -> list[tuple[datetime, float]]:
    scored = [(e.timestamp, e.mood_score) for e in entries if e.mood_score is not None]
    return sorted(scored, key=lambda pair: pair[0])


def most_common_words(entries: list[JournalEntry], top_n: int = 10) -> list[tuple[str, int]]:
    stopwords = {
        "the", "a", "an", "and", "or", "but", "to", "of", "in", "on", "at",
        "is", "was", "were", "it", "i", "for", "with", "my", "me", "that",
        "this", "be", "as", "so", "im", "i'm", "you", "your", "am", "are",
        "feel", "feeling", "feelings", "felt", "today", "day", "very",
        "just", "really", "about", "have", "has", "had", "not", "all",
        "some", "then", "too", "there", "here", "what", "when", "if",
        "everything", "something", "anything", "again", "even", "still",
    }
    counter: Counter[str] = Counter()
    for entry in entries:
        words = [w.strip(".,!?;:\"'()").lower() for w in entry.text.split()]
        counter.update(w for w in words if w and w not in stopwords)
    return counter.most_common(top_n)


def streak_days(entries: list[JournalEntry]) -> int:
    if not entries:
        return 0
    dates = sorted({e.timestamp.date() for e in entries}, reverse=True)
    today = datetime.now().date()
    if (today - dates[0]).days > 1:
        return 0
    streak = 1
    for prev, curr in zip(dates, dates[1:]):
        if (prev - curr).days == 1:
            streak += 1
        else:
            break
    return streak


def generate_smart_insight(entries: list[JournalEntry]) -> str:
    """Free, offline alternative to an LLM-generated reflection: detects
    real patterns (dominant emotions, mood swings, recurring themes,
    streaks) and writes them up in natural sentences using templates.
    """
    if not entries:
        return "No entries yet - write a few first, then check back for a reflection."

    recent = entries[:14]
    sentences = []

    emotion_totals: dict[str, float] = {}
    for e in recent:
        for emotion, score in e.emotions.items():
            emotion_totals[emotion] = emotion_totals.get(emotion, 0) + score
    top_emotions = sorted(
        (item for item in emotion_totals.items() if item[1] > 0),
        key=lambda kv: -kv[1],
    )[:2]

    if top_emotions:
        if len(top_emotions) == 1:
            sentences.append(f"Lately, {top_emotions[0][0]} has been the clearest thread running through your entries.")
        else:
            sentences.append(
                f"Two feelings keep showing up: {top_emotions[0][0]} and {top_emotions[1][0]}. "
                "Worth noticing whether they tend to appear together or in response to different things."
            )
    else:
        sentences.append("Your recent entries read fairly even-keeled, without one emotion dominating.")

    scored = [e.mood_score for e in reversed(recent) if e.mood_score is not None]
    if len(scored) >= 4:
        first_half = sum(scored[: len(scored) // 2]) / (len(scored) // 2)
        second_half = sum(scored[len(scored) // 2 :]) / (len(scored) - len(scored) // 2)
        delta = second_half - first_half
        if delta > 0.25:
            sentences.append("Your mood has been trending upward across these entries - whatever's shifted seems to be helping.")
        elif delta < -0.25:
            sentences.append("There's a downward drift in mood across these entries - this might be worth paying attention to.")

    streak = streak_days(entries)
    if streak >= 3:
        sentences.append(f"You're {streak} days into a writing streak - consistency like that tends to make patterns easier to spot over time.")
    elif streak == 0:
        sentences.append("It's been a little while since your last entry - even a short one can help keep the thread going.")

    top_words = most_common_words(recent, top_n=3)
    if top_words:
        words_str = ", ".join(w for w, _ in top_words)
        sentences.append(f"Recurring words in these entries: {words_str} - might be worth asking yourself why those keep coming up.")

    return " ".join(sentences)


def generate_summary(entries: list[JournalEntry]) -> str:
    if not entries:
        return "No entries yet - write your first one to see insights."

    avg = average_mood(entries)
    label = mood_label(avg)
    streak = streak_days(entries)
    top_words = most_common_words(entries, top_n=5)
    words_str = ", ".join(w for w, _ in top_words) if top_words else "n/a"

    lines = [
        f"Entries analyzed: {len(entries)}",
        f"Average mood: {label} ({avg:.2f})" if avg is not None else "Average mood: not enough data",
        f"Current streak: {streak} day(s)",
        f"Frequently mentioned: {words_str}",
    ]
    return "\n".join(lines)