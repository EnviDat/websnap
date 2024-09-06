"""Tests for src/websnap/logger.py"""

import logging
import pytest

from websnap.logger import (
    get_custom_logger,
    get_log_level,
    get_console_handler,
    get_file_handler,
)


def test_get_custom_logger(log_config_model):

    log = get_custom_logger(
        name="websnap_logger", config=log_config_model, file_logs=True
    )
    assert isinstance(log, logging.Logger)

    file_handler_exists = False
    for handler in log.handlers:
        if isinstance(handler, logging.FileHandler):
            file_handler_exists = True

    assert file_handler_exists


@pytest.mark.parametrize(
    "log_level, expected",
    [
        ("DEBUG", 10),
        ("INFO", 20),
        ("WARNING", 30),
        ("ERROR", 40),
        ("CRITICAL", 50),
        ("random_string", 20),
    ],
)
def test_get_log_level(log_level, expected):
    assert get_log_level(log_level) == expected


def test_get_console_handler():
    assert isinstance(get_console_handler(), logging.StreamHandler)


@pytest.mark.parametrize(
    "filename, when, interval, backup",
    [("websnap1.log", "D", 1, 1), ("websnap2.log", "midnight", 2, 3)],
)
def test_get_log_config(filename, when, interval, backup):
    file_handler = get_file_handler(filename, when, interval, backup)
    assert isinstance(file_handler, logging.FileHandler)
