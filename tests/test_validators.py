"""Tests for src/websnap/validators.py"""

import configparser
from pathlib import Path

import pytest

from websnap.validators import (
    is_url,
    merge_config_parsers,
    get_json_config_parser,
    get_url_json_config_parser,
    get_json_section_config_parser,
    get_config_parser,
    validate_positive_integer,
    validate_s3_config_section,
    S3ConfigSectionModel,
)


@pytest.mark.parametrize("x", [1, 0, 1.23, "abc"])
def test_validate_positive_integer(x):
    try:
        result = validate_positive_integer(x)
        assert result == x
    except Exception as e:
        if e == f"{x} is not a positive integer":
            assert True


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


def test_merge_config_parsers(config_parser_basic, config_parser_log, config_parser_s3):
    result_1 = merge_config_parsers(config_parser_basic, config_parser_log)
    assert isinstance(result_1, configparser.ConfigParser)

    result_2 = merge_config_parsers(config_parser_basic, config_parser_s3)
    assert isinstance(result_2, configparser.ConfigParser)


def test_json_config_parser(config_basic):
    result = get_json_config_parser(config_basic[0])
    assert isinstance(result, configparser.ConfigParser)


def test_json_config_parser_nonexistent_config():
    with pytest.raises(Exception):
        get_json_config_parser(Path("nonexistent_config.json"))


def test_get_url_json_config_parser():
    result_1 = get_url_json_config_parser(
        "https://www.envidat.ch/converters-api/internal-dataset/websnap-config-all/"
        "bibtex?bucket=random&is-recent=true&is-json=true",
        30,
    )
    assert isinstance(result_1, configparser.ConfigParser)

    with pytest.raises(Exception):
        get_url_json_config_parser("https://httpbin.org/status/400", 30)


def test_get_json_section_config_parser():
    result = get_json_section_config_parser(
        "https://www.envidat.ch/converters-api/internal-dataset/websnap-config-all/"
        "bibtex?bucket=random&is-recent=true&is-json=true",
        30,
    )
    assert isinstance(result, configparser.ConfigParser)


@pytest.mark.parametrize(
    "section_config", ["section_config.ini", "section_config.json"]
)
def test_get_json_section_config_parser_invalid_section_config(section_config):
    with pytest.raises(Exception):
        get_json_section_config_parser(section_config)


def test_get_config_parser(config_basic):
    result = get_config_parser(config=config_basic[0], timeout=30)
    assert isinstance(result, configparser.ConfigParser)


@pytest.mark.parametrize(
    "config, section_config, timeout",
    [
        ("config_1.ini", "section_config.ini", 30),
        ("config_2.json", "section_config.json", 30),
    ],
)
def test_get_config_parser_invalid_parameters(config, section_config, timeout):
    with pytest.raises(Exception):
        get_config_parser(config=config, section_config=section_config, timeout=timeout)


def test_get_config_parser_invalid_section_config(config_basic):
    with pytest.raises(Exception):
        get_config_parser(
            config=config_basic[0], section_config="non-existent.json", timeout=30
        )


def test_validate_s3_config_section(config_parser_s3):
    result = validate_s3_config_section(config_parser_s3, "pypi-websnap-s3")
    assert isinstance(result, S3ConfigSectionModel)


@pytest.mark.parametrize(
    "section",
    ["pypi-websnap-s3_invalid_key", "pypi-websnap-s3_invalid_key2", "no-bucket"],
)
def test_validate_s3_config_section_invalid_section(section, config_parser_s3_invalid):
    result = validate_s3_config_section(config_parser_s3_invalid, section)
    assert not isinstance(result, S3ConfigSectionModel)
