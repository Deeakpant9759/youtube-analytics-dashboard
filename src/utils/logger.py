import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(
    logger_name: str = "youtube_dashboard", 
    log_file: str = "logs/app.log",
    level: int = logging.INFO
) -> logging.Logger:
    """
    Create and return production-ready logger.

    Features:
    - File logging
    - Console logging
    - Rotating log files
    - Prevent duplicate handlers
    """

    # Create logs folder if missing
    Path("logs").mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(logger_name)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(level)

    log_format = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | "
        "File:%(filename)s | Line:%(lineno)d | %(message)s"
    )

    # File Handler (5 MB x 3 backups)
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(log_format)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("Logger initialized successfully.")

    return logger


# Global logger instance
logger = setup_logger()