"""Tests for src/websnap/validators.py"""

import configparser
import pytest

from websnap.validators import (
    is_url,
    merge_config_parsers,
    get_json_config_parser,
    get_url_json_config_parser,
    get_json_section_config_parser,
    get_config_parser,
)


@pytest.mark.parametrize(
    "x, expected",
    [
        ("https://pypi.org/pypi/websnap/json", True),
        ("A most lovely string", False),
        (1, False),
        (True, False),
        (None, False),
    ],
)
def test_is_url(x, expected):
    result = is_url(x)
    assert result == expected


def test_merge_config_parsers(config_parser_basic, config_parser_log):
    result = merge_config_parsers(config_parser_basic, config_parser_log)
    assert isinstance(result, configparser.ConfigParser)


def test_json_config_parser(config_basic):
    result = get_json_config_parser(config_basic[0])
    assert isinstance(result, configparser.ConfigParser)


def test_get_url_json_config_parser():
    result = get_url_json_config_parser(
        "https://www.envidat.ch/converters-api/internal-dataset/websnap-config-all/"
        "bibtex?bucket=random&is-recent=true&is-json=true",
        30,
    )
    assert isinstance(result, configparser.ConfigParser)


def test_get_json_section_config_parser():
    result = get_json_section_config_parser(
        "https://www.envidat.ch/converters-api/internal-dataset/websnap-config-all/"
        "bibtex?bucket=random&is-recent=true&is-json=true",
        30,
    )
    assert isinstance(result, configparser.ConfigParser)


def test_get_config_parser(config_basic, config_parser_log):

    result = get_config_parser(config=config_basic[0], timeout=30)
    assert isinstance(result, configparser.ConfigParser)
