"""Tests for src/websnap/validators.py"""

import configparser
import json
from pathlib import Path

import pytest
from unittest.mock import patch, ANY, MagicMock

import requests
from pydantic import ValidationError

from websnap.validators import (
    is_url,
    merge_config_parsers,
    get_json_config_parser,
    get_url_json_config_parser,
    get_json_section_config_parser,
    get_config_parser,
    validate_timeout,
    validate_backup_s3_count,
    validate_s3_config_section,
    S3ConfigSectionModel,
    validate_endpoint_url,
    validate_log_config,
    validate_min_size_kb,
    validate_config_section,
)


@pytest.mark.parametrize("timeout", [1, 10, 100])
def test_validate_timeout_valid(timeout):
    validate_timeout(timeout)


@pytest.mark.parametrize("timeout", [0, -1, -100])
def test_validate_timeout_invalid(timeout):
    with pytest.raises(ValueError):
        validate_timeout(timeout)


@pytest.mark.parametrize("backup_s3_count", [1, 5, 100])
def test_validate_backup_s3_count_valid(backup_s3_count):
    validate_backup_s3_count(backup_s3_count)


def test_validate_backup_s3_count_none():
    validate_backup_s3_count(None)


@pytest.mark.parametrize("backup_s3_count", [0, -1, -100])
def test_validate_backup_s3_count_invalid(backup_s3_count):
    with pytest.raises(ValueError):
        validate_backup_s3_count(backup_s3_count)


def test_validate_endpoint_url():
    assert validate_endpoint_url("https://cloud.com/", True) == "https://cloud.com/"
    assert validate_endpoint_url(None, False) is None


def test_validate_endpoint_url_no_url():
    with pytest.raises(ValueError):
        validate_endpoint_url(None, True)


def test_validate_endpoint_url_invalid():
    with pytest.raises(ValueError):
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
    with pytest.raises(FileNotFoundError):
        get_json_config_parser(Path("nonexistent_config.json"))


def test_get_json_config_parser_invalid_json(tmp_path):
    broken_file = tmp_path / "broken.json"
    broken_file.write_text("{ 'invalid': json }")

    with pytest.raises(ValueError):
        get_json_config_parser(broken_file)


@patch("websnap.validators.make_session")
def test_get_url_json_config_parser_timeout(mock_make_session):
    url = "https://example.com"
    timeout_val = 5
    mock_make_session.return_value.get.side_effect = requests.exceptions.Timeout()

    with pytest.raises(TimeoutError):
        get_url_json_config_parser(url, timeout=timeout_val)


@patch("websnap.validators.make_session")
def test_get_url_json_config_parser(mock_make_session):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "Section1": {"url": "https://example.com", "file_name": "test.json"}
    }
    mock_make_session.return_value.get.return_value = mock_response

    result = get_url_json_config_parser("https://example.com", 30)
    assert isinstance(result, configparser.ConfigParser)


@patch("websnap.validators.make_session")
def test_get_url_json_config_parser_http_error(mock_make_session):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        response=MagicMock(status_code=400)
    )
    mock_make_session.return_value.get.return_value = mock_response

    with pytest.raises(RuntimeError):
        get_url_json_config_parser("https://example.com", 30)


@patch("websnap.validators.make_session")
def test_get_url_json_config_parser_json_error(mock_make_session):
    url = "https://example.com"

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
    mock_make_session.return_value.get.return_value = mock_response

    with pytest.raises(ValueError):
        get_url_json_config_parser(url)


@patch("websnap.validators.make_session")
def test_get_url_json_config_parser_request_exception(mock_make_session):
    url = "https://invalid-domain.xyz"

    mock_make_session.return_value.get.side_effect = (
        requests.exceptions.RequestException("DNS failure")
    )

    with pytest.raises(ConnectionError):
        get_url_json_config_parser(url)


@patch("websnap.validators.get_url_json_config_parser")
def test_get_json_section_config_parser(mock_get_url):
    parser = configparser.ConfigParser()
    parser.add_section("Section1")
    mock_get_url.return_value = parser

    result = get_json_section_config_parser("https://example.com", 30)
    assert isinstance(result, configparser.ConfigParser)


def test_get_json_section_config_parser_invalid_extension():
    """
    Test that ValueError is raised when the section_config
    file does not end in '.json'.
    """
    invalid_file = "config.txt"

    with pytest.raises(ValueError):
        get_json_section_config_parser(invalid_file)


@patch("websnap.validators.is_url")
@patch("websnap.validators.get_json_config_parser")
def test_get_json_section_config_parser_not_instance(mock_get_json, mock_is_url):
    mock_is_url.return_value = False
    mock_get_json.return_value = "I am a string, not a parser"

    with pytest.raises(TypeError):
        get_json_section_config_parser("test.json")


@patch("websnap.validators.is_url")
@patch("websnap.validators.get_json_config_parser")
def test_get_json_section_config_parser_has_defaults(mock_get_json, mock_is_url):
    mock_is_url.return_value = False

    parser_with_defaults = configparser.ConfigParser()
    parser_with_defaults["DEFAULT"] = {"key": "value"}
    mock_get_json.return_value = parser_with_defaults

    with pytest.raises(ValueError):
        get_json_section_config_parser("test.json")


def test_get_config_parser(config_basic):
    result = get_config_parser(config=config_basic[0], timeout=30)
    assert isinstance(result, configparser.ConfigParser)


@pytest.mark.parametrize(
    "config, section_config, timeout",
    [
        ("config_1.ini", "section_config.ini", 30),
        ("config_2.ini", "section_config.json", 30),
    ],
)
def test_get_config_parser_invalid_parameters(config, section_config, timeout):
    with pytest.raises(ValueError):
        get_config_parser(config=config, section_config=section_config, timeout=timeout)


def test_get_config_parser_invalid_section_config(config_basic):
    with pytest.raises(FileNotFoundError):
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

    with pytest.raises(FileNotFoundError):
        get_config_parser(str(missing_ini))


def test_get_config_parser_no_sections_error(tmp_path):
    empty_conf = tmp_path / "empty.ini"
    empty_conf.write_text("# This file only has comments\n# No sections here.")

    with pytest.raises(ValueError):
        get_config_parser(str(empty_conf))


def test_validate_s3_config_section(config_parser_s3):
    result = validate_s3_config_section(config_parser_s3, "pypi-websnap-s3")
    assert isinstance(result, S3ConfigSectionModel)


@pytest.mark.parametrize(
    "section",
    ["pypi-websnap-s3_invalid_key", "pypi-websnap-s3_invalid_key2", "no-bucket"],
)
def test_validate_s3_config_section_invalid_section(section, config_parser_s3_invalid):
    with pytest.raises(ValueError):
        validate_s3_config_section(config_parser_s3_invalid, section)


@patch("websnap.validators.LogConfigModel")
def test_validate_log_config_validation_error(mock_model):
    parser = configparser.ConfigParser()
    mock_model.side_effect = ValidationError.from_exception_data("TestModel", [])

    with pytest.raises(ValueError):
        validate_log_config(parser)


def test_validate_log_config_value_error():
    parser = configparser.ConfigParser()
    parser.set("DEFAULT", "log_interval", "not-a-number")

    with pytest.raises(ValueError):
        validate_log_config(parser)


def test_validate_min_size_kb_success():
    parser = configparser.ConfigParser()
    parser.set("DEFAULT", "min_size_kb", "1024")

    assert validate_min_size_kb(parser) == 1024


def test_validate_min_size_kb_negative_error():
    parser = configparser.ConfigParser()
    parser.set("DEFAULT", "min_size_kb", "-50")

    with pytest.raises(ValueError):
        validate_min_size_kb(parser)


def test_validate_min_size_kb_type_error():
    """Test that a noninteger string triggers the getint ValueError and sys.exit."""
    parser = configparser.ConfigParser()
    parser.set("DEFAULT", "min_size_kb", "not-a-number")

    with pytest.raises(ValueError):
        validate_min_size_kb(parser)


def test_validate_min_size_kb_fallback():
    """Test that the fallback value is used if the key is missing."""
    parser = configparser.ConfigParser()

    # No 'min_size_kb' set
    # This assumes MIN_SIZE_KB is defined in your module (e.g., 0)
    result = validate_min_size_kb(parser)
    assert isinstance(result, int)


def test_validate_config_section_missing_option():
    """Test when a required key like 'url' is missing."""
    parser = configparser.ConfigParser()
    parser.add_section("Section1")
    # 'url' and 'file_name' are missing

    with pytest.raises(ValueError):
        validate_config_section(parser, "Section1")


def test_validate_config_section_invalid_url():
    """Test when 'url' exists but fails Pydantic validation (AnyHttpUrl)."""
    parser = configparser.ConfigParser()
    parser.add_section("Section1")
    parser.set("Section1", "url", "not-a-url")
    parser.set("Section1", "file_name", "test.txt")

    with pytest.raises(ValueError):
        validate_config_section(parser, "Section1")


def test_validate_config_section_no_section():
    """Test when the requested section doesn't exist at all."""
    parser = configparser.ConfigParser()

    with pytest.raises(ValueError):
        validate_config_section(parser, "NonExistentSection")
