"""
Supports rotational logging.
"""

import logging
import sys
from enum import Enum
from logging.handlers import TimedRotatingFileHandler

WHEN_INTERVAL = "midnight"
# TODO revert
# WHEN_INTERVAL = "W6"
BACKUP_COUNT = 7


class LogFormatter(Enum):
    """Class with values used to format logs."""

    FORMAT = "%(asctime)s | %(levelname)s | %(message)s"
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


def get_log_level(log_level: str = "INFO"):
    """
    Return logging level for logger. Default log level: logging.INFO

    Args:
        log_level(str): logging level represented as upper case string, default log
                    level is 'INFO'
    """
    match log_level:
        case LogLevel.DEBUG.value:
            level = logging.DEBUG
        case LogLevel.WARNING.value:
            level = logging.WARNING
        case LogLevel.ERROR.value:
            level = logging.ERROR
        case LogLevel.CRITICAL.value:
            level = logging.CRITICAL
        case LogLevel.INFO.value | _:
            level = logging.INFO

    return level


def get_console_handler() -> logging.StreamHandler:
    """
    Return formatted console handler.
    """
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(LogFormatter.formatter())
    return console_handler


def get_file_handler(filename: str) -> logging.handlers.TimedRotatingFileHandler:
    """
    Return formatted rotational file handler for logs.
    Repeat interval, backup count and formatter
    are set with constants at beginning of module.

    Args:
        filename (str): name of logger file
    """
    file_handler = TimedRotatingFileHandler(
        filename, when=WHEN_INTERVAL, backupCount=BACKUP_COUNT
    )
    file_handler.setFormatter(LogFormatter.formatter())
    return file_handler


def get_logger(logger_name: str, loglevel: str = "INFO") -> logging.getLogger:
    """
    Return logger with console and file handlers added. Default logging level is
    'INFO'.

    Args:
        logger_name (str): name of logger
        loglevel(str): logging level represented as upper case string, default log
                    level is 'INFO'
    """
    # TODO test
    try:
        _loglevel = loglevel.upper()
    except AttributeError:
        raise Exception("Argument loglevel must be a string")

    logger = logging.getLogger(logger_name)
    logger.setLevel(get_log_level(_loglevel))
    logger.addHandler(get_console_handler())
    logger.addHandler(get_file_handler(f"{logger_name}.log"))
    logger.propagate = False  # TODO review

    return logger
