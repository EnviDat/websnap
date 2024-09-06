"""
Logging utilities, console handlers, and rotational file handlers.
"""

import logging
from logging.handlers import TimedRotatingFileHandler
import sys

from websnap.validators import LogConfigModel
from websnap.constants import LogFormatter, LogLevel


def get_log_level(log_level: str = "INFO") -> int:
    """
    Return logging level for logger. Default log level: logging.INFO

    Args:
        log_level: logging level represented as upper case string

    Returns:
        Integer that corresponds to logging level.
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


def get_file_handler(
    filename: str, when: str, interval: int, backup_count: int
) -> logging.handlers.TimedRotatingFileHandler:
    """
    Return formatted rotational file handler for logs.
    To learn more about logging TimedRotating FileHandler and the values acceptable for
     'when' and how to use interval and backupCount see:
    https://docs.python.org/3/library/logging.handlers.html#timedrotatingfilehandler

    Args:
        filename: Name of log file.
        when: Value used to assign when logs rotate.
        interval: How frequently to rotate logs.
        backup_count: If more than 0 then at most <backup_count> files will be kept.
    """
    file_handler = TimedRotatingFileHandler(
        filename=filename, when=when, interval=interval, backupCount=backup_count
    )
    file_handler.setFormatter(LogFormatter.formatter())
    return file_handler


def get_custom_logger(
    name: str,
    config: LogConfigModel,
    level: str = "INFO",
    file_logs: bool = False,
) -> logging.getLogger:
    """
    Return logger with console handler and optional file handler.
    Default logging level is 'INFO'.

    Args:
        name: Name of logger.
        config: Validated log config.
        level: Logging level represented as string.
        file_logs: If True then implements rotating file logs.
    """
    try:
        _loglevel = level.upper()
    except AttributeError:  # pragma: no cover
        raise Exception("Argument loglevel must be a string")

    logger = logging.getLogger(name)
    logger.setLevel(get_log_level(_loglevel))
    logger.addHandler(get_console_handler())

    if file_logs:
        logger.addHandler(
            get_file_handler(
                filename=f"{name}.log",
                when=config.log_when,
                interval=config.log_interval,
                backup_count=config.log_backup_count,
            )
        )

    logger.propagate = False

    return logger
