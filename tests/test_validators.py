"""Tests for src/websnap/validators.py"""

import configparser
from pathlib import Path

import pytest
from unittest.mock import patch, ANY

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
    validate_endpoint_url,
    validate_positive_int_args,
)


@pytest.mark.parametrize("x", [1, 0, 1.23, "abc"])
def test_validate_positive_integer(x):
    try:
        result = validate_positive_integer(x)
        assert result == x
    except ValueError as e:
        if e == f"Argument is not a a positive integer: {x}":
            assert True

@pytest.mark.parametrize("timeout, backup_s3_count", [(-1, None), (2, -3)])
def test_validate_positive_int_args(timeout, backup_s3_count):
    with pytest.raises(SystemExit):
        assert validate_positive_int_args(timeout, backup_s3_count)


def test_validate_endpoint_url():
    assert validate_endpoint_url("https://cloud.com/", True) == "https://cloud.com/"
    assert validate_endpoint_url(None, False) is None


def test_validate_endpoint_url_no_url():
    with pytest.raises(SystemExit):
        validate_endpoint_url(None, True)


def test_validate_endpoint_url_invalid():
    with pytest.raises(SystemExit):
        validate_endpoint_url("abc", True)


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
    with pytest.raises(SystemExit):
        get_json_config_parser(Path("nonexistent_config.json"))


def test_get_json_config_parser_invalid_json(tmp_path):
    broken_file = tmp_path / "broken.json"
    broken_file.write_text("{ 'invalid': json }")

    with pytest.raises(SystemExit):
        get_json_config_parser(broken_file)


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
    with pytest.raises(SystemExit):
        get_json_section_config_parser(section_config)


@patch("websnap.validators.is_url")
@patch("websnap.validators.get_json_config_parser")
def test_get_json_section_config_parser_not_instance(mock_get_json, mock_is_url):
    mock_is_url.return_value = False
    mock_get_json.return_value = "I am a string, not a parser"

    with pytest.raises(SystemExit):
        get_json_section_config_parser("test.json")


@patch("websnap.validators.is_url")
@patch("websnap.validators.get_json_config_parser")
def test_get_json_section_config_parser_has_defaults(mock_get_json, mock_is_url):
    mock_is_url.return_value = False

    parser_with_defaults = configparser.ConfigParser()
    parser_with_defaults['DEFAULT'] = {'key': 'value'}
    mock_get_json.return_value = parser_with_defaults

    with pytest.raises(SystemExit):
        get_json_section_config_parser("test.json")


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
    with pytest.raises(SystemExit):
        get_config_parser(config=config, section_config=section_config, timeout=timeout)


def test_get_config_parser_invalid_section_config(config_basic):
    with pytest.raises(SystemExit):
        get_config_parser(
            config=config_basic[0], section_config="non-existent.json", timeout=30
        )


def test_get_config_parser_ini_success(tmp_path):
    ini_file = tmp_path / "settings.ini"
    ini_content = "[Section1]\nkey1 = value1"
    ini_file.write_text(ini_content)

    parser = get_config_parser(str(ini_file))

    assert isinstance(parser, configparser.ConfigParser)
    assert parser.get("Section1", "key1") == "value1"


@patch("websnap.validators.get_json_config_parser")
@patch("websnap.validators.get_json_section_config_parser")
@patch("websnap.validators.merge_config_parsers")
def test_get_config_parser_merges_successfully(
        mock_merge, mock_get_section, mock_get_main
):
    main_parser = configparser.ConfigParser()
    main_parser.add_section("MainSection")

    section_parser = configparser.ConfigParser()
    section_parser.add_section("ExtraSection")

    mock_get_main.return_value = main_parser
    mock_get_section.return_value = section_parser

    merged_parser = configparser.ConfigParser()
    merged_parser.add_section("MainSection")
    merged_parser.add_section("ExtraSection")
    mock_merge.return_value = merged_parser

    result = get_config_parser("base.json", section_config="extra.json")

    mock_get_main.assert_called_once()
    mock_get_section.assert_called_once_with("extra.json", ANY)

    mock_merge.assert_called_once_with(main_parser, section_parser)

    assert "MainSection" in result.sections()
    assert "ExtraSection" in result.sections()


def test_get_config_parser_ini_file_not_found(tmp_path):
    missing_ini = tmp_path / "does_not_exist.ini"

    with pytest.raises(SystemExit):
        get_config_parser(str(missing_ini))


def test_get_config_parser_no_sections_error(tmp_path):
    empty_conf = tmp_path / "empty.ini"
    empty_conf.write_text("# This file only has comments\n# No sections here.")

    with pytest.raises(SystemExit):
        get_config_parser(str(empty_conf))


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
