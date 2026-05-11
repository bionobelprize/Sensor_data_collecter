from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from sensor_collector.config import LoggingConfig


def setup_logging(cfg: LoggingConfig) -> logging.Logger:
    logger = logging.getLogger("sensor_collector")
    logger.setLevel(cfg.level.upper())
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    Path(cfg.log_dir).mkdir(parents=True, exist_ok=True)
    log_path = Path(cfg.log_dir) / cfg.log_file

    file_handler = RotatingFileHandler(log_path, maxBytes=10 * 1024 * 1024, backupCount=10)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
