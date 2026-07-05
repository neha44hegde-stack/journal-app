import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import JournalEntry
from storage import SQLiteStorage


class TestSQLiteStorage(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmpdir.name, "test.db")
        self.storage = SQLiteStorage(self.db_path)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_add_and_get_by_id(self):
        entry = JournalEntry(text="first entry")
        saved = self.storage.add_entry(entry)
        self.assertIsNotNone(saved.id)

        fetched = self.storage.get_by_id(saved.id)
        self.assertEqual(fetched.text, "first entry")

    def test_get_all_returns_newest_first(self):
        self.storage.add_entry(JournalEntry(text="older"))
        self.storage.add_entry(JournalEntry(text="newer"))
        entries = self.storage.get_all()
        self.assertEqual(len(entries), 2)
        texts = {e.text for e in entries}
        self.assertEqual(texts, {"older", "newer"})

    def test_update_mood_score(self):
        entry = self.storage.add_entry(JournalEntry(text="entry"))
        self.storage.update_mood_score(entry.id, 0.75)
        fetched = self.storage.get_by_id(entry.id)
        self.assertEqual(fetched.mood_score, 0.75)

    def test_delete_entry(self):
        entry = self.storage.add_entry(JournalEntry(text="to delete"))
        result = self.storage.delete_entry(entry.id)
        self.assertTrue(result)
        self.assertIsNone(self.storage.get_by_id(entry.id))

    def test_delete_nonexistent_entry_returns_false(self):
        self.assertFalse(self.storage.delete_entry(9999))

    def test_search_finds_matching_entries(self):
        self.storage.add_entry(JournalEntry(text="I went hiking today"))
        self.storage.add_entry(JournalEntry(text="Just relaxed at home"))
        results = self.storage.search("hiking")
        self.assertEqual(len(results), 1)
        self.assertIn("hiking", results[0].text)

    def test_search_no_match_returns_empty(self):
        self.storage.add_entry(JournalEntry(text="nothing relevant here"))
        results = self.storage.search("zzz_no_such_word")
        self.assertEqual(results, [])

    def test_iter_all_yields_all_entries(self):
        for i in range(3):
            self.storage.add_entry(JournalEntry(text=f"entry {i}"))
        collected = list(self.storage.iter_all())
        self.assertEqual(len(collected), 3)


if __name__ == "__main__":
    unittest.main()