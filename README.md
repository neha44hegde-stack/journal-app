# Secure Journal App

An encrypted, searchable command-line journal that goes beyond simple mood
tracking — it detects 16 distinct emotions in your writing, visualizes
patterns on an interactive dashboard, and generates written reflections
on recurring themes, all without sending your data anywhere (unless you
opt into the AI reflection feature).

## Features

- **Encrypted at rest** — entries are encrypted with Fernet (AES-128 +
  HMAC), key derived from your password via PBKDF2-HMAC (480,000
  iterations). No password recovery, by design — if you forget it, old
  entries are unreadable.
- **Full-text search** — SQLite with an FTS5 index for fast search over
  entry contents.
- **16-emotion detection** — joy, sadness, anger, anxiety, fear, calm,
  love, surprise, disgust, shame, guilt, pride, hope, boredom, gratitude,
  and loneliness, scored independently per entry (multiple emotions can
  be present at once, since real feelings rarely fit one label).
- **Visual dashboard** — a self-contained HTML report with a GitHub-style
  calendar heatmap (colored by each day's dominant emotion) and an
  emotion-totals breakdown. Opens directly in your browser.
- **Free, offline reflections** — a pattern-detection engine surfaces
  mood trends, recurring emotions, journaling streaks, and recurring
  topics, written up in plain language, at zero cost.
- **Optional AI-generated reflections** — if you set an Anthropic API
  key, the app can instead ask Claude for a more nuanced written
  reflection on your recent entries.
- **Edit and delete**, with confirmation prompts to prevent accidental
  data loss.
- **Tags** — optionally tag entries at write time for future filtering.

## Project structure
## Setup

```bash
pip install cryptography
python cli.py
```

First run asks you to set a master password — this derives your
encryption key and is never stored anywhere. Every subsequent run asks
you to unlock with the same password.

## Optional: enable AI-generated reflections

Set an environment variable with your [Anthropic API key](https://console.anthropic.com):

```bash
export ANTHROPIC_API_KEY="sk-ant-..."      # macOS/Linux
$env:ANTHROPIC_API_KEY = "sk-ant-..."      # Windows PowerShell
```

Without a key set, the app automatically falls back to the free,
offline reflection engine — no functionality is lost.

## Optional: better sentiment scoring

The built-in mood scorer is a dependency-free keyword-based analyzer.
For more accurate sentiment analysis:

```bash
pip install vaderSentiment
```

No code changes needed — this is detected and used automatically if
installed.

## Running tests

```bash
python -m unittest discover -s tests -v
```

## Design notes

- **Storage is behind an abstract interface** (`storage.py`), so the
  SQLite backend could be swapped for a cloud database without touching
  any other module.
- **Search on encrypted data is a real tradeoff**: SQLite's FTS5 index
  needs plaintext to be useful, so once entries are encrypted, search
  decrypts and scans in Python rather than using the DB-level index.
  Fine for a personal journal's scale, not for a huge corpus.
- **Mood score is computed before encryption** and stored as a plain
  float alongside the ciphertext, so analytics never needs to decrypt
  entries just to compute aggregate stats — a deliberate tradeoff of
  score-privacy for analytics speed.