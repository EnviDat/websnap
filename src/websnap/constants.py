"""Enums and constants."""

import logging
from enum import Enum


TIMEOUT: int = 32
MIN_SIZE_KB: int = 0


class LogFormatter(Enum):
    """Class with values used to format logs."""

    FORMAT = (
        "%(asctime)s | %(levelname)s | %(module)s.%(funcName)s:%(lineno)d | %(message)s"
    )
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    @classmethod
    def formatter(cls):
        return logging.Formatter(fmt=cls.FORMAT.value, datefmt=cls.DATE_FORMAT.value)


class LogLevel(Enum):
    """Class with supported log levels."""

    DEBUG = "DEBUG"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    INFO = "INFO"


class LogRotation(Enum):
    """Class with default values used by rotating file logs."""

    WHEN = "D"
    INTERVAL = 1
    BACKUP_COUNT = 0
