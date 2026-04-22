"""Tests for src/websnap/logic.py"""

import configparser
from datetime import datetime
from unittest.mock import patch, mock_open, MagicMock

import pytest
import requests
from botocore.exceptions import (
    ClientError,
    BotoCoreError,
    NoCredentialsError,
    EndpointConnectionError,
)

from websnap.logger import get_custom_logger
from websnap.logic import (
    terminate_program,
    get_url_content,
    is_min_size_kb,
    write_urls_locally,
    handle_s3_client_error,
    copy_s3_object,
    delete_s3_backup_object,
    create_s3_client,
    validate_bucket_access,
    write_urls_to_s3,
)


@pytest.fixture
def log_logic(log_config_model):
    return get_custom_logger(name="websnap_logic", config=log_config_model)


@pytest.fixture
def url_content_pypi_websnap(log_logic):
    return get_url_content(
        "https://pypi.org/pypi/websnap/json", "pypi-websnap", log_logic
    )


@pytest.mark.parametrize(
    "url, section, expected",
    [
        ("https://httpbin.org/status/400", "error-response", None),
        ("https://pypi.org/pypi/websnap/json", "pypi-websnap", bytes),
    ],
)
def test_get_url_content(url, section, expected, log_logic):

    result = get_url_content(url, section, log_logic)

    if expected is None:
        assert result is None
    else:
        assert isinstance(result, expected)


@patch("websnap.logic.requests.get")
@patch("websnap.logic.terminate_program")
def test_get_url_content_timeout(mock_terminate, mock_get):
    """Test that timeout logs error and calls terminate_program."""
    url = "https://example.com"
    section = "TestSection"
    timeout_val = 10
    log = MagicMock()

    mock_get.side_effect = requests.exceptions.Timeout()

    result = get_url_content(url, section, log, timeout=timeout_val, early_exit=True)

    assert result is None

    mock_terminate.assert_called_once_with(True)


@patch("websnap.logic.requests.get")
@patch("websnap.logic.terminate_program")
def test_get_url_content_timeout_no_exit(mock_terminate, mock_get):
    """Test that timeout returns None without crashing when early_exit is False."""
    log = MagicMock()
    mock_get.side_effect = requests.exceptions.Timeout()

    result = get_url_content("http://url.com", "S1", log, early_exit=False)

    assert result is None

    mock_terminate.assert_called_once_with(False)


@pytest.mark.parametrize(
    "min_size_kb, section, expected",
    [
        (1, "pypi-websnap", True),
        (50000, "pypi-websnap", False),
    ],
)
def test_is_min_size_kb(
    min_size_kb, section, expected, log_logic, url_content_pypi_websnap
):

    result = is_min_size_kb(
        url_content=url_content_pypi_websnap,
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
        url="http://test.com", file_name="file.txt", directory="downloads"
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
    mock_deps["isdir"].return_value = False  # Directory check fails
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
    mock_deps["min_size"].return_value = False  # Size check fails
    log = MagicMock()

    write_urls_locally(parser, log, min_size_kb=100)

    # Content was fetched but file was never opened/written
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

    # Mock validation success but download failure
    mock_validate.return_value = MagicMock(directory=None, file_name="test.txt")
    mock_get_url.return_value = None  # <--- Triggers "if not url_content"

    log = MagicMock()
    write_urls_locally(parser, log, min_size_kb=1)

    # Assert: it called get_url_content but never tried to open/write a file
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

    # Assert: open was called with just the filename, not a directory prefix
    mock_file.assert_called_once_with("local_only.txt", "wb")
    log.info.assert_called_with(
        "Successfully downloaded URL content and wrote file locally in "
        "config section: NoDirSection"
    )


@pytest.fixture
def mock_client_error():
    """Helper to create a ClientError with a specific status code."""

    def _create_error(status_code):
        error_response = {
            "ResponseMetadata": {"HTTPStatusCode": status_code},
            "Error": {"Code": "SomeError", "Message": "Some message"},
        }
        return ClientError(error_response, "S3Operation")

    return _create_error


@patch("websnap.logic.terminate_program")
def test_handle_s3_error_404(mock_terminate, mock_client_error):
    """Test 404 logs a warning and does NOT terminate."""
    log = MagicMock()
    err = mock_client_error(404)

    handle_s3_client_error(err, log, "TestSection", early_exit=True)

    log.warning.assert_called_once_with(
        "Config section 'TestSection': Object not found"
    )
    mock_terminate.assert_not_called()


@patch("websnap.logic.terminate_program")
def test_handle_s3_error_403(mock_terminate, mock_client_error):
    """Test 403 logs an error and triggers termination."""
    log = MagicMock()
    err = mock_client_error(403)

    handle_s3_client_error(err, log, "TestSection", early_exit=True)

    assert "Forbidden" in log.error.call_args[0][0]
    mock_terminate.assert_called_once_with(True)


@patch("websnap.logic.terminate_program")
def test_handle_s3_error_generic(mock_terminate, mock_client_error):
    """Test other status codes (e.g., 500) log the error and terminate."""
    log = MagicMock()
    err = mock_client_error(500)

    handle_s3_client_error(err, log, "TestSection", early_exit=False)

    # Verify the actual error object was logged
    log.error.assert_called_once_with(err)
    mock_terminate.assert_called_once_with(False)


@pytest.fixture
def mock_s3_conf():
    """Returns a valid S3 config model mock."""
    return MagicMock(bucket="my-bucket", key="data.txt")


@patch("websnap.logic.terminate_program")
def test_copy_s3_object_unexpected_status(mock_terminate, mock_s3_conf):
    """Test the 'else' branch when S3 returns a non-200 code."""
    log = MagicMock()
    client = MagicMock()

    client.head_object.return_value = {"LastModified": datetime(2023, 1, 1, 12, 0, 0)}

    client.copy_object.return_value = {"ResponseMetadata": {"HTTPStatusCode": 500}}

    copy_s3_object(client, mock_s3_conf, log, "TestSection", early_exit=True)

    assert "unexpected HTTP response 500" in log.error.call_args[0][0]
    mock_terminate.assert_called_once_with(True)


@patch("websnap.logic.handle_s3_client_error")
def test_copy_s3_object_client_error(mock_handler, mock_s3_conf):
    """Test the 'except ClientError' block."""
    log = MagicMock()
    client = MagicMock()

    err_resp = {"Error": {"Code": "AccessDenied", "Message": "Forbidden"}}
    err = ClientError(err_resp, "HeadObject")

    client.head_object.side_effect = err

    copy_s3_object(client, mock_s3_conf, log, "TestSection", early_exit=False)

    mock_handler.assert_called_once_with(err, log, "TestSection", False)


def test_delete_s3_backup_object_no_prefix():
    """Test list_objects_v2 is called without Prefix when key has no directory."""
    client = MagicMock()
    log = MagicMock()

    # Mock config with a key that has no "/"
    mock_conf = MagicMock()
    mock_conf.bucket = "my-bucket"
    mock_conf.key = "file.txt"  # No slashes here

    # Mock S3 response to avoid errors in the rest of the function
    client.list_objects_v2.return_value = {"Contents": []}

    delete_s3_backup_object(
        client, mock_conf, log, section="TestSection", backup_s3_count=3
    )

    # Check that list_objects_v2 was called with Bucket but with no Prefix
    client.list_objects_v2.assert_called_once_with(Bucket="my-bucket")

    # Verify it was not called with the Prefix argument
    args, kwargs = client.list_objects_v2.call_args
    assert "Prefix" not in kwargs


@patch("websnap.logic.handle_s3_client_error")
def test_delete_s3_backup_object_client_error(mock_handler):
    """Test the 'except ClientError' block when an S3 call fails."""
    log = MagicMock()
    client = MagicMock()
    section = "S3_Backup_Section"
    early_exit = False

    mock_conf = MagicMock()
    mock_conf.bucket = "my-bucket"
    mock_conf.key = "folder/data.txt"

    error_response = {
        "Error": {"Code": "NoSuchBucket", "Message": "Bucket does not exist"}
    }
    err = ClientError(error_response, "ListObjectsV2")
    client.list_objects_v2.side_effect = err

    delete_s3_backup_object(
        client, mock_conf, log, section, backup_s3_count=3, early_exit=early_exit
    )

    # Verify the dedicated error handler was called with the original error
    mock_handler.assert_called_once_with(err, log, section, early_exit)


@pytest.mark.parametrize(
    "exception_to_raise",
    [
        BotoCoreError(),
        NoCredentialsError(),
        EndpointConnectionError(endpoint_url="http://invalid"),
    ],
)
@patch("websnap.logic.boto3.Session")
def test_create_s3_client_exceptions(mock_session_class, exception_to_raise):
    """Test that BotoCore, NoCredentials, and Endpoint errors trigger SystemExit."""
    mock_session_instance = MagicMock()
    mock_session_class.return_value = mock_session_instance

    mock_session_instance.client.side_effect = exception_to_raise

    with pytest.raises(SystemExit):
        create_s3_client(endpoint_url="http://localhost:4566")


def test_validate_bucket_access_triggers_value_error():
    """Test that a ClientError from S3 triggers a ValueError."""
    mock_client = MagicMock()

    error_response = {"Error": {"Code": "403", "Message": "Forbidden"}}
    client_error = ClientError(error_response, "HeadBucket")

    mock_client.head_bucket.side_effect = client_error

    with pytest.raises(ValueError):
        validate_bucket_access(mock_client, "my-secret-bucket")


@patch("websnap.logic.validate_s3_config_section")
@patch("websnap.logic.terminate_program")
def test_write_urls_to_s3_value_error(mock_terminate, mock_validate_s3):
    """Test that a ValueError logs correctly and triggers termination logic."""
    parser = configparser.ConfigParser()
    parser.add_section("MySection")

    # 2. Mock validation to raise a ValueError
    mock_validate_s3.side_effect = ValueError("Missing URL")

    log = MagicMock()
    client = MagicMock()

    write_urls_to_s3(parser, client, log, min_size_kb=1, early_exit=True)

    log.error.assert_called_once_with(
        "Validation failed for config section 'MySection': Missing URL"
    )

    mock_terminate.assert_called_once_with(True)


@patch("websnap.logic.validate_s3_config_section")
@patch("websnap.logic.validate_bucket_access")
@patch("websnap.logic.terminate_program")
def test_write_urls_to_s3_bucket_access_error(
    mock_terminate, mock_bucket_access, mock_validate_s3
):
    """Test that a ValueError from bucket access triggers termination logic."""
    parser = configparser.ConfigParser()
    parser.add_section("Section2")

    # Mock validate_s3 to pass, but bucket access to fail
    mock_validate_s3.return_value = MagicMock(bucket="test-bucket")
    mock_bucket_access.side_effect = ValueError("Access Denied")

    log = MagicMock()

    write_urls_to_s3(parser, MagicMock(), log, min_size_kb=1, early_exit=False)

    log.error.assert_called_once_with(
        "Validation failed for config section 'Section2': Access Denied"
    )
    mock_terminate.assert_called_once_with(False)


@patch("websnap.logic.validate_s3_config_section")
@patch("websnap.logic.validate_bucket_access")
@patch("websnap.logic.get_url_content")
@patch("websnap.logic.terminate_program")
def test_write_urls_to_s3_skips_on_no_url_content(
    mock_terminate, mock_get_url, mock_bucket_access, mock_validate_s3
):
    """Test that the loop continues/skips when url_content is None."""
    parser = configparser.ConfigParser()
    parser.add_section("DownloadFailSection")

    # Mock Validation and Bucket Access to succeed
    mock_conf = MagicMock()
    mock_conf.url = "https://example.com"
    mock_conf.bucket = "my-bucket"
    mock_validate_s3.return_value = mock_conf
    mock_bucket_access.return_value = None

    # Trigger the skip: Mock get_url_content to return None
    mock_get_url.return_value = None

    log = MagicMock()
    client = MagicMock()

    # 4. Execute
    write_urls_to_s3(parser, client, log, min_size_kb=1)

    mock_get_url.assert_called_once()

    # Verify no further action was taken
    assert log.info.call_count == 0
    mock_terminate.assert_not_called()


@patch("websnap.logic.validate_s3_config_section")
@patch("websnap.logic.validate_bucket_access")
@patch("websnap.logic.get_url_content")
@patch("websnap.logic.is_min_size_kb")
@patch("websnap.logic.terminate_program")
def test_write_urls_to_s3_skips_on_min_size_failure(
    mock_terminate, mock_is_min_size, mock_get_url, mock_bucket_access, mock_validate_s3
):
    """Test that the loop skips to the next section if the file is too small."""
    parser = configparser.ConfigParser()
    parser.add_section("SmallFileSection")

    # Mock Validation and Bucket Access to succeed
    mock_conf = MagicMock()
    mock_conf.url = "https://example.com"
    mock_conf.bucket = "my-bucket"
    mock_validate_s3.return_value = mock_conf
    mock_bucket_access.return_value = None

    # Mock download to succeed
    mock_get_url.return_value = b"tiny content"

    # Trigger the skip:  Mock is_min_size_kb to return False
    mock_is_min_size.return_value = False

    log = MagicMock()
    client = MagicMock()

    write_urls_to_s3(parser, client, log, min_size_kb=100)

    # Verify the size check was performed
    mock_is_min_size.assert_called_once()

    # Verify no further action was taken
    assert log.info.call_count == 0
    mock_terminate.assert_not_called()


@patch("websnap.logic.validate_s3_config_section")
@patch("websnap.logic.validate_bucket_access")
@patch("websnap.logic.get_url_content")
@patch("websnap.logic.is_min_size_kb")
@patch("websnap.logic.handle_s3_client_error")
def test_write_urls_to_s3_skips_after_put_error(
    mock_handler, mock_min_size, mock_get_url, mock_bucket_access, mock_validate_s3
):
    """Verify that a PutObject failure in Section 1 doesn't stop Section 2."""
    # Setup Parser with two sections
    parser = configparser.ConfigParser()
    parser.add_section("SectionFail")
    parser.add_section("SectionSuccess")

    # Setup successful mocks
    mock_conf = MagicMock(bucket="my-bucket", key="data.bin", url="http://test.com")
    mock_validate_s3.return_value = mock_conf
    mock_bucket_access.return_value = None
    mock_get_url.return_value = b"valid content"
    mock_min_size.return_value = True

    client = MagicMock()

    # Mock put_object: First call fails (ClientError), Second call succeeds
    err = ClientError({"Error": {"Code": "403", "Message": "Forbidden"}}, "PutObject")
    success_resp = {"ResponseMetadata": {"HTTPStatusCode": 200}}
    client.put_object.side_effect = [err, success_resp]

    log = MagicMock()

    write_urls_to_s3(parser, client, log, min_size_kb=1)

    # Verify put_object was attempted twice (once for each section)
    assert client.put_object.call_count == 2

    # Verify the failure was logged for the first section
    mock_handler.assert_called_once_with(err, log, "SectionFail", False)

    # Verify the second section finished successfully
    log.info.assert_called_with(
        "Config section 'SectionSuccess': Successfully copied URL "
        "content to S3 object 'data.bin'"
    )
