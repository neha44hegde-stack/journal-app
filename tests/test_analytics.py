import sys
import os
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics import (
    LexiconAnalyzer,
    average_mood,
    generate_summary,
    mood_label,
    mood_trend,
    most_common_words,
    streak_days,
)
from models import JournalEntry


class TestLexiconAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = LexiconAnalyzer()

    def test_positive_text_scores_positive(self):
        score = self.analyzer.score("I am so happy and grateful today, wonderful day")
        self.assertGreater(score, 0)

    def test_negative_text_scores_negative(self):
        score = self.analyzer.score("I feel sad and anxious and stressed")
        self.assertLess(score, 0)

    def test_neutral_text_scores_zero(self):
        score = self.analyzer.score("I went to the store and bought some groceries")
        self.assertEqual(score, 0.0)

    def test_empty_text_scores_zero(self):
        self.assertEqual(self.analyzer.score(""), 0.0)


class TestMoodLabel(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(mood_label(0.5), "positive")
        self.assertEqual(mood_label(-0.5), "negative")
        self.assertEqual(mood_label(0.0), "neutral")
        self.assertEqual(mood_label(None), "unscored")


class TestAggregateInsights(unittest.TestCase):
    def test_average_mood(self):
        entries = [
            JournalEntry(text="a", mood_score=1.0),
            JournalEntry(text="b", mood_score=-1.0),
            JournalEntry(text="c", mood_score=None),
        ]
        self.assertEqual(average_mood(entries), 0.0)

    def test_average_mood_no_scores(self):
        entries = [JournalEntry(text="a", mood_score=None)]
        self.assertIsNone(average_mood(entries))

    def test_mood_trend_sorted_chronologically(self):
        now = datetime.now()
        entries = [
            JournalEntry(text="b", timestamp=now, mood_score=0.5),
            JournalEntry(text="a", timestamp=now - timedelta(days=1), mood_score=-0.5),
        ]
        trend = mood_trend(entries)
        self.assertEqual(trend[0][1], -0.5)
        self.assertEqual(trend[1][1], 0.5)

    def test_most_common_words_ignores_stopwords(self):
        entries = [JournalEntry(text="the cat sat on the mat and the cat ran")]
        common = most_common_words(entries, top_n=3)
        words = [w for w, _ in common]
        self.assertIn("cat", words)
        self.assertNotIn("the", words)

    def test_streak_days_consecutive(self):
        today = datetime.now()
        entries = [
            JournalEntry(text="a", timestamp=today),
            JournalEntry(text="b", timestamp=today - timedelta(days=1)),
            JournalEntry(text="c", timestamp=today - timedelta(days=2)),
        ]
        self.assertEqual(streak_days(entries), 3)

    def test_streak_days_broken(self):
        today = datetime.now()
        entries = [
            JournalEntry(text="a", timestamp=today),
            JournalEntry(text="b", timestamp=today - timedelta(days=5)),
        ]
        self.assertEqual(streak_days(entries), 1)

    def test_streak_days_empty(self):
        self.assertEqual(streak_days([]), 0)

    def test_generate_summary_no_entries(self):
        summary = generate_summary([])
        self.assertIn("No entries yet", summary)

    def test_generate_summary_with_entries(self):
        entries = [JournalEntry(text="a good day", mood_score=0.8)]
        summary = generate_summary(entries)
        self.assertIn("Entries analyzed: 1", summary)


if __name__ == "__main__":
    unittest.main()