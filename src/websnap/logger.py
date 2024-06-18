"""
Supports rotational logging.
"""

import logging
import sys
from logging.handlers import TimedRotatingFileHandler


WHEN_INTERVAL = "midnight"
# TODO revert
# WHEN_INTERVAL = "W6"
BACKUP_COUNT = 7
FORMATTER = logging.Formatter(
    fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)


def get_console_handler() -> logging.StreamHandler:
    """
    Return formatted console handler. Formatter is set with constant at beginning
    of module.
    """
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
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
    file_handler.setFormatter(FORMATTER)
    return file_handler


def set_log_level(logger: logging.getLogger, log_level: str = "INFO"):
    """
    Set logging level for logger. Default log level: logging.INFO

    Args:
    logger: logger instance
    log_level(str): logging level represented as upper case string, default log
                level is 'INFO'
    """
    match log_level:
        case "DEBUG":
            logger.setLevel(logging.DEBUG)
        case "WARNING":
            logger.setLevel(logging.WARNING)
        case "ERROR":
            logger.setLevel(logging.ERROR)
        case "CRITICAL":
            logger.setLevel(logging.CRITICAL)
        case "INFO" | _:
            logger.setLevel(logging.INFO)


def get_logger(logger_name: str, log_level: str = "INFO") -> logging.getLogger:
    """
    Return logger with console and file handlers added. Default logging level is
    'INFO'.

    Args:
        logger_name (str): name of logger
        log_level(str): logging level represented as upper case string, default log
                    level is 'INFO'
    """
    logger = logging.getLogger(logger_name)
    set_log_level(logger, log_level)
    logger.addHandler(get_console_handler())
    logger.addHandler(get_file_handler(f"{logger_name}.log"))
    logger.propagate = False
    return logger
