"""Tests for src/websnap/logger.py"""

import logging
import pytest

from websnap.logger import get_custom_logger, get_log_level, get_console_handler
from websnap.validators import get_config_parser, validate_log_config


@pytest.fixture
def config_parser_log(config_log):
    return get_config_parser(config_log[0])


@pytest.fixture
def log_config_model(config_parser_log):
    return validate_log_config(config_parser_log)


def test_get_custom_logger(log_config_model):
    log = get_custom_logger(name="websnap", config=log_config_model, file_logs=True)

    assert isinstance(log, logging.Logger)

    file_handler_exists = False
    for handler in log.handlers:
        if isinstance(handler, logging.FileHandler):
            file_handler_exists = True

    assert file_handler_exists


def test_get_log_level():
    assert isinstance(get_log_level(), int)


def test_get_console_handler():
    assert isinstance(get_console_handler(), logging.StreamHandler)
