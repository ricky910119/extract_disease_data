from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from config.settings import LOG_DIR, PROJECT_NAME


def build_run_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def setup_logger(run_id: str | None = None) -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if run_id is None:
        run_id = build_run_id()

    logger = logging.getLogger(PROJECT_NAME)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(
        LOG_DIR / f"{PROJECT_NAME}_{run_id}.log",
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    stream_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger
