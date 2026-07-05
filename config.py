"""
Centralized configuration, loaded from environment variables with sane defaults.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    db_path: str = os.getenv("JOURNAL_DB_PATH", "journal.db")
    salt_path: str = os.getenv("JOURNAL_SALT_PATH", "salt.bin")
    log_level: str = os.getenv("JOURNAL_LOG_LEVEL", "INFO")
    log_path: str = os.getenv("JOURNAL_LOG_PATH", "journal_app.log")
    pbkdf2_iterations: int = int(os.getenv("JOURNAL_PBKDF2_ITERATIONS", "480000"))
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    ai_model: str = os.getenv("JOURNAL_AI_MODEL", "claude-sonnet-4-6")


settings = Settings()