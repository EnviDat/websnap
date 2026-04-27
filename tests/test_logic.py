"""Tests for src/websnap/logic.py"""

import configparser
from unittest.mock import patch, mock_open, MagicMock

import pytest
import requests

from websnap.logger import get_custom_logger
from websnap.logic import (
    terminate_program,
    get_url_content,
    is_min_size_kb,
    write_urls_locally,
)


@pytest.fixture
def log_logic(log_config_model):
    return get_custom_logger(name="websnap_logic", config=log_config_model)


@pytest.fixture
def url_content_bytes():
    return b"x" * 2048


@patch("websnap.logic.make_session")
def test_get_url_content_success(mock_make_session, log_logic):
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.content = b"data"
    mock_make_session.return_value.get.return_value = mock_response

    result = get_url_content("https://example.com", "S1", log_logic)

    assert result == b"data"


@patch("websnap.logic.make_session")
def test_get_url_content_non_ok(mock_make_session, log_logic):
    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.status_code = 400
    mock_make_session.return_value.get.return_value = mock_response

    result = get_url_content("https://example.com", "S1", log_logic)

    assert result is None


@patch("websnap.logic.terminate_program")
@patch("websnap.logic.make_session")
def test_get_url_content_timeout(mock_make_session, mock_terminate):
    """Test that timeout logs error and calls terminate_program."""
    log = MagicMock()
    mock_make_session.return_value.get.side_effect = requests.exceptions.Timeout()

    result = get_url_content(
        "https://example.com", "TestSection", log, timeout=10, early_exit=True
    )

    assert result is None
    mock_terminate.assert_called_once_with(True)


@patch("websnap.logic.terminate_program")
@patch("websnap.logic.make_session")
def test_get_url_content_timeout_no_exit(mock_make_session, mock_terminate):
    """Test that timeout returns None without crashing when early_exit is False."""
    log = MagicMock()
    mock_make_session.return_value.get.side_effect = requests.exceptions.Timeout()

    result = get_url_content("https://example.com", "S1", log, early_exit=False)

    assert result is None
    mock_terminate.assert_called_once_with(False)


@patch("websnap.logic.terminate_program")
@patch("websnap.logic.make_session")
def test_get_url_content_ssl_error_no_exit(mock_make_session, mock_terminate):
    """Test that SSLError returns None without crashing when early_exit is False."""
    log = MagicMock()
    mock_make_session.return_value.get.side_effect = requests.exceptions.SSLError()

    result = get_url_content("https://example.com", "S1", log, early_exit=False)

    assert result is None
    mock_terminate.assert_called_once_with(False)


@patch("websnap.logic.terminate_program")
@patch("websnap.logic.make_session")
def test_get_url_content_connection_error_no_exit(mock_make_session, mock_terminate):
    """Test that ConnectionError returns None without crashing when early_exit is False."""
    log = MagicMock()
    mock_make_session.return_value.get.side_effect = (
        requests.exceptions.ConnectionError()
    )

    result = get_url_content("https://example.com", "S1", log, early_exit=False)

    assert result is None
    mock_terminate.assert_called_once_with(False)


@patch("websnap.logic.terminate_program")
@patch("websnap.logic.make_session")
def test_get_url_content_request_exception_no_exit(mock_make_session, mock_terminate):
    """Test that RequestException returns None without crashing when early_exit is False."""
    log = MagicMock()
    mock_make_session.return_value.get.side_effect = (
        requests.exceptions.RequestException()
    )

    result = get_url_content("https://example.com", "S1", log, early_exit=False)

    assert result is None
    mock_terminate.assert_called_once_with(False)


@pytest.mark.parametrize(
    "min_size_kb, section, expected",
    [
        (1, "pypi-websnap", True),
        (50000, "pypi-websnap", False),
    ],
)
def test_is_min_size_kb(min_size_kb, section, expected, log_logic, url_content_bytes):
    result = is_min_size_kb(
        url_content=url_content_bytes,
        min_size_kb=min_size_kb,
        section=section,
        log=log_logic,
    )
    assert result == expected


def test_terminate_program():
    assert terminate_program(False) is None


def test_terminate_program_exit():
    with pytest.raises(SystemExit):
        terminate_program(True)


@pytest.fixture
def mock_deps():
    """Fixture to group all patches for cleaner tests."""
    with (
        patch("websnap.logic.validate_config_section") as v_section,
        patch("websnap.logic.os.path.isdir") as isdir,
        patch("websnap.logic.get_url_content") as get_content,
        patch("websnap.logic.is_min_size_kb") as min_size,
        patch("websnap.logic.terminate_program") as terminate,
        patch("builtins.open", mock_open()) as m_open,
    ):
        yield {
            "validate": v_section,
            "isdir": isdir,
            "get_content": get_content,
            "min_size": min_size,
            "terminate": terminate,
            "open": m_open,
        }


def test_write_urls_locally_success(mock_deps):
    """Test successful download and file write for multiple sections."""
    parser = configparser.ConfigParser()
    parser.add_section("Section1")
    parser.add_section("Section2")

    mock_conf = MagicMock(
        url="https://test.com", file_name="file.txt", directory="downloads"
    )
    mock_deps["validate"].return_value = mock_conf
    mock_deps["isdir"].return_value = True
    mock_deps["get_content"].return_value = b"test content"
    mock_deps["min_size"].return_value = True

    log = MagicMock()

    write_urls_locally(parser, log, min_size_kb=1)

    assert mock_deps["open"].call_count == 2
    mock_deps["open"].assert_any_call("downloads/file.txt", "wb")
    assert log.info.call_count == 2


def test_write_urls_locally_validation_error(mock_deps):
    """Test that a ValueError in validation logs an error and terminates."""
    parser = configparser.ConfigParser()
    parser.add_section("BadSection")

    mock_deps["validate"].side_effect = ValueError("Invalid Config")
    log = MagicMock()

    write_urls_locally(parser, log, min_size_kb=1, early_exit=True)

    log.error.assert_called_once_with(mock_deps["validate"].side_effect)
    mock_deps["terminate"].assert_called_once_with(True)


def test_write_urls_locally_missing_directory(mock_deps):
    """Test scenario where the specified directory does not exist."""
    parser = configparser.ConfigParser()
    parser.add_section("MissingDir")

    mock_conf = MagicMock(directory="invalid_path", file_name="f.txt")
    mock_deps["validate"].return_value = mock_conf
    mock_deps["isdir"].return_value = False
    log = MagicMock()

    write_urls_locally(parser, log, min_size_kb=1)

    assert "does not exist" in log.error.call_args[0][0]
    assert mock_deps["get_content"].call_count == 0


def test_write_urls_locally_min_size_fail(mock_deps):
    """Test that it skips writing if the file is too small."""
    parser = configparser.ConfigParser()
    parser.add_section("SmallFile")

    mock_conf = MagicMock(directory=None, file_name="small.txt")
    mock_deps["validate"].return_value = mock_conf
    mock_deps["get_content"].return_value = b"tiny"
    mock_deps["min_size"].return_value = False
    log = MagicMock()

    write_urls_locally(parser, log, min_size_kb=100)

    mock_deps["get_content"].assert_called_once()
    assert mock_deps["open"].call_count == 0


@patch("websnap.logic.get_url_content")
@patch("websnap.logic.validate_config_section")
@patch("builtins.open", new_callable=mock_open)
def test_write_urls_locally_skips_on_empty_content(
    mock_file, mock_validate, mock_get_url
):
    """Test that the loop continues/skips if url_content is None."""
    parser = configparser.ConfigParser()
    parser.add_section("FailSection")

    mock_validate.return_value = MagicMock(directory=None, file_name="test.txt")
    mock_get_url.return_value = None

    log = MagicMock()
    write_urls_locally(parser, log, min_size_kb=1)

    mock_get_url.assert_called_once()
    mock_file.assert_not_called()


@patch("websnap.logic.is_min_size_kb")
@patch("websnap.logic.get_url_content")
@patch("websnap.logic.validate_config_section")
@patch("builtins.open", new_callable=mock_open)
def test_write_urls_locally_no_directory_path(
    mock_file, mock_validate, mock_get_url, mock_min_size
):
    """Test file path construction when directory is None."""
    parser = configparser.ConfigParser()
    parser.add_section("NoDirSection")

    mock_validate.return_value = MagicMock(directory=None, file_name="local_only.txt")
    mock_get_url.return_value = b"some data"
    mock_min_size.return_value = True

    log = MagicMock()
    write_urls_locally(parser, log, min_size_kb=1)

    mock_file.assert_called_once_with("local_only.txt", "wb")
    log.info.assert_called_with(
        "Successfully downloaded URL content and wrote file locally in "
        "config section: NoDirSection"
    )
