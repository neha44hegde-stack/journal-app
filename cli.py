"""
CLI entry point for the journal app. Run with: python cli.py
"""
from __future__ import annotations

import getpass
import sys
import webbrowser
from pathlib import Path

from ai_insights import AIInsightError, generate_ai_insight
from analytics import generate_smart_insight, generate_summary, get_default_analyzer, mood_label, mood_trend
from config import settings
from dashboard import generate_dashboard_html
from emotions import detect_emotions
from encrypted_storage import EncryptedJournalStorage
from logging_config import get_logger
from models import JournalEntry
from security import JournalCipher, WrongPasswordError, get_or_create_salt
from storage import SQLiteStorage

logger = get_logger(__name__)
DB_PATH = settings.db_path
SALT_PATH = settings.salt_path


def unlock() -> EncryptedJournalStorage:
    salt = get_or_create_salt(SALT_PATH)
    is_new_journal = not Path(DB_PATH).exists()

    if is_new_journal:
        print("No journal found - let's set a master password to secure it.")
        pw1 = getpass.getpass("Create a master password: ")
        pw2 = getpass.getpass("Confirm password: ")
        if pw1 != pw2:
            print("Passwords didn't match. Please restart.")
            sys.exit(1)
        password = pw1
    else:
        password = getpass.getpass("Enter your master password: ")

    cipher = JournalCipher(password, salt)
    raw_storage = SQLiteStorage(DB_PATH)
    storage = EncryptedJournalStorage(raw_storage, cipher)

    if not is_new_journal:
        existing = raw_storage.get_all()
        if existing:
            try:
                cipher.decrypt(existing[0].text)
            except WrongPasswordError:
                logger.warning("Failed unlock attempt (wrong password)")
                print("Incorrect password.")
                sys.exit(1)

    return storage


def write_entry(storage: EncryptedJournalStorage) -> None:
    print("Enter your journal entry (blank line or 'exit' to finish):")
    lines = []
    while True:
        line = input("> ")
        if line.strip().lower() == "exit" or line == "":
            break
        lines.append(line)

    if not lines:
        print("No entry was made.")
        return

    text = "\n".join(lines)

    tag_input = input("Tags (comma-separated, optional): ").strip()
    tags = [t.strip() for t in tag_input.split(",") if t.strip()] if tag_input else []

    analyzer = get_default_analyzer()
    mood_score = analyzer.score(text)
    emotion_profile = detect_emotions(text)

    entry = JournalEntry(text=text, mood_score=mood_score, emotions=emotion_profile.to_dict(), tags=tags)
    storage.add_entry(entry)

    print(f"Saved. Detected mood: {mood_label(mood_score)} ({mood_score:.2f})")
    if emotion_profile.dominant != "neutral":
        print(f"Dominant emotion: {emotion_profile.dominant}")


def read_journal(storage: EncryptedJournalStorage) -> None:
    entries = storage.get_all()
    if not entries:
        print("No entries yet.")
        return
    for entry in entries:
        print("\n" + "=" * 40)
        print(f"[{entry.id}] {entry.timestamp:%Y-%m-%d %H:%M} - mood: {mood_label(entry.mood_score)}")
        if entry.tags:
            print(f"Tags: {', '.join(entry.tags)}")
        print("=" * 40)
        print(entry.text)


def search_journal(storage: EncryptedJournalStorage) -> None:
    query = input("Search for: ").strip()
    if not query:
        return
    results = storage.search(query)
    if not results:
        print("No matching entries.")
        return
    print(f"\nFound {len(results)} match(es):")
    for entry in results:
        print(f"  [{entry.id}] {entry.timestamp:%Y-%m-%d %H:%M} - {entry.preview()}")


def show_insights(storage: EncryptedJournalStorage) -> None:
    entries = storage.get_all()
    print("\n--- Journal Insights ---")
    print(generate_summary(entries))

    trend = mood_trend(entries)
    if len(trend) >= 2:
        print("\nMood trend (oldest to newest):")
        for ts, score in trend:
            bar = "#" * int((score + 1) * 10)
            print(f"  {ts:%Y-%m-%d}  {bar:<20} {score:+.2f}")


def show_ai_insight(storage: EncryptedJournalStorage) -> None:
    entries = storage.get_all()

    if settings.anthropic_api_key:
        print("\nAsking Claude for a reflection on your recent entries...")
        try:
            insight = generate_ai_insight(entries)
            print("\n--- AI Reflection ---")
            print(insight)
            return
        except AIInsightError as e:
            print(f"\nAPI reflection failed ({e}). Falling back to the free local reflection.")

    print("\n--- Reflection (free, offline) ---")
    print(generate_smart_insight(entries))


def open_dashboard(storage: EncryptedJournalStorage) -> None:
    entries = storage.get_all()
    if not entries:
        print("No entries yet - write some first.")
        return
    path = generate_dashboard_html(entries)
    print(f"Dashboard written to {path}")
    try:
        webbrowser.open(f"file://{Path(path).resolve()}")
    except Exception:
        print("Couldn't auto-open a browser - open the file manually.")


def edit_entry(storage: EncryptedJournalStorage) -> None:
    try:
        entry_id = int(input("Entry ID to edit: ").strip())
    except ValueError:
        print("Please enter a valid numeric ID.")
        return

    entry = storage.get_by_id(entry_id)
    if not entry:
        print(f"No entry found with ID {entry_id}.")
        return

    print("\nCurrent text:")
    print(entry.text)
    print("\nEnter new text (blank line or 'exit' to finish, replaces the entry entirely):")
    lines = []
    while True:
        line = input("> ")
        if line.strip().lower() == "exit" or line == "":
            break
        lines.append(line)

    if not lines:
        print("No changes made.")
        return

    new_text = "\n".join(lines)
    if storage.update_entry_text(entry_id, new_text):
        print(f"Entry {entry_id} updated.")
    else:
        print("Update failed.")


def delete_entry(storage: EncryptedJournalStorage) -> None:
    try:
        entry_id = int(input("Entry ID to delete: ").strip())
    except ValueError:
        print("Please enter a valid numeric ID.")
        return

    entry = storage.get_by_id(entry_id)
    if not entry:
        print(f"No entry found with ID {entry_id}.")
        return

    print(f"\nAbout to permanently delete entry [{entry_id}]:")
    print(f"  {entry.preview()}")
    confirm = input("Type 'yes' to confirm deletion: ").strip().lower()
    if confirm != "yes":
        print("Deletion cancelled.")
        return

    if storage.delete_entry(entry_id):
        print(f"Entry {entry_id} deleted.")
    else:
        print(f"No entry found with ID {entry_id}.")


def main() -> None:
    storage = unlock()
    print("\nJournal unlocked.")

    menu = {
        "1": ("Write a new entry", write_entry),
        "2": ("Read your journal", read_journal),
        "3": ("Search entries", search_journal),
        "4": ("View insights & mood trend", show_insights),
        "5": ("Open emotion dashboard (browser)", open_dashboard),
        "6": ("Get a reflection on your entries (free)", show_ai_insight),
        "7": ("Edit an entry", edit_entry),
        "8": ("Delete an entry", delete_entry),
        "9": ("Exit", None),
    }

    while True:
        print("\n--- Secure Journal ---")
        for key, (label, _) in menu.items():
            print(f"{key}. {label}")
        choice = input("Choose an option: ").strip()

        if choice == "9":
            print("Goodbye.")
            break
        elif choice in menu:
            menu[choice][1](storage)
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()