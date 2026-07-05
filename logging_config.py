"""
Logging setup. Never logs journal text or passwords - only metadata.
"""
from __future__ import annotations

import logging

from config import settings


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(settings.log_level)

    file_handler = logging.FileHandler(settings.log_path)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    logger.addHandler(file_handler)
    return logger