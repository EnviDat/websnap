"""Tests for src/websnap/logic_s3.py"""

import configparser
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest
from botocore.exceptions import (
    ClientError,
    BotoCoreError,
    NoCredentialsError,
    EndpointConnectionError,
)

from websnap.logic_s3 import (
    handle_s3_client_error,
    copy_s3_object,
    delete_s3_backup_object,
    create_s3_client,
    validate_bucket_access,
    write_urls_to_s3,
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


@pytest.fixture
def mock_s3_conf():
    """Returns a valid S3 config model mock."""
    return MagicMock(bucket="my-bucket", key="data.txt")


@patch("websnap.logic_s3.terminate_program")
def test_handle_s3_error_404(mock_terminate, mock_client_error):
    """Test 404 logs a warning and does NOT terminate."""
    log = MagicMock()
    err = mock_client_error(404)

    handle_s3_client_error(err, log, "TestSection", early_exit=True)

    log.warning.assert_called_once_with(
        "Config section 'TestSection': Object not found"
    )
    mock_terminate.assert_not_called()


@patch("websnap.logic_s3.terminate_program")
def test_handle_s3_error_403(mock_terminate, mock_client_error):
    """Test 403 logs an error and triggers termination."""
    log = MagicMock()
    err = mock_client_error(403)

    handle_s3_client_error(err, log, "TestSection", early_exit=True)

    assert "Forbidden" in log.error.call_args[0][0]
    mock_terminate.assert_called_once_with(True)


@patch("websnap.logic_s3.terminate_program")
def test_handle_s3_error_generic(mock_terminate, mock_client_error):
    """Test other status codes (e.g., 500) log the error and terminate."""
    log = MagicMock()
    err = mock_client_error(500)

    handle_s3_client_error(err, log, "TestSection", early_exit=False)

    log.error.assert_called_once_with(err)
    mock_terminate.assert_called_once_with(False)


@patch("websnap.logic_s3.terminate_program")
def test_copy_s3_object_unexpected_status(mock_terminate, mock_s3_conf):
    """Test the 'else' branch when S3 returns a non-200 code."""
    log = MagicMock()
    client = MagicMock()

    client.head_object.return_value = {"LastModified": datetime(2023, 1, 1, 12, 0, 0)}
    client.copy_object.return_value = {"ResponseMetadata": {"HTTPStatusCode": 500}}

    copy_s3_object(client, mock_s3_conf, log, "TestSection", early_exit=True)

    assert "unexpected HTTP response 500" in log.error.call_args[0][0]
    mock_terminate.assert_called_once_with(True)


@patch("websnap.logic_s3.handle_s3_client_error")
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

    mock_conf = MagicMock()
    mock_conf.bucket = "my-bucket"
    mock_conf.key = "file.txt"

    client.list_objects_v2.return_value = {"Contents": []}

    delete_s3_backup_object(
        client, mock_conf, log, section="TestSection", backup_s3_count=3
    )

    client.list_objects_v2.assert_called_once_with(Bucket="my-bucket")
    args, kwargs = client.list_objects_v2.call_args
    assert "Prefix" not in kwargs


@patch("websnap.logic_s3.terminate_program")
def test_delete_s3_backup_object_unexpected_status(mock_terminate):
    """Test the else branch when delete_object returns a non-204 status."""
    client = MagicMock()
    log = MagicMock()
    section = "S3_Delete_Section"

    mock_conf = MagicMock()
    mock_conf.bucket = "my-bucket"
    mock_conf.key = "folder/data.txt"

    client.list_objects_v2.return_value = {
        "Contents": [
            {
                "Key": "folder/data_2023-01-01_10-00-00.txt",
                "LastModified": datetime(2023, 1, 1),
            },
            {
                "Key": "folder/data_2023-01-02_10-00-00.txt",
                "LastModified": datetime(2023, 1, 2),
            },
        ]
    }
    client.delete_object.return_value = {"ResponseMetadata": {"HTTPStatusCode": 500}}

    delete_s3_backup_object(
        client, mock_conf, log, section, backup_s3_count=1, early_exit=True
    )

    log.error.assert_called_once_with(
        f"Config section '{section}': Backup file delete "
        f"attempt returned unexpected HTTP response 500"
    )
    mock_terminate.assert_called_once_with(True)


@patch("websnap.logic_s3.handle_s3_client_error")
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

    mock_handler.assert_called_once_with(err, log, section, early_exit)


@pytest.mark.parametrize(
    "exception_to_raise",
    [
        BotoCoreError(),
        NoCredentialsError(),
        EndpointConnectionError(endpoint_url="http://invalid"),
    ],
)
@patch("websnap.logic_s3.boto3.Session")
def test_create_s3_client_exceptions(mock_session_class, exception_to_raise):
    """Test that BotoCore, NoCredentials, and Endpoint errors trigger ConnectionError."""
    mock_session_instance = MagicMock()
    mock_session_class.return_value = mock_session_instance
    mock_session_instance.client.side_effect = exception_to_raise

    with pytest.raises(ConnectionError):
        create_s3_client(endpoint_url="http://localhost:4566")


def test_validate_bucket_access_triggers_value_error():
    """Test that a ClientError from S3 triggers a ValueError."""
    mock_client = MagicMock()

    error_response = {"Error": {"Code": "403", "Message": "Forbidden"}}
    client_error = ClientError(error_response, "HeadBucket")
    mock_client.head_bucket.side_effect = client_error

    with pytest.raises(ValueError):
        validate_bucket_access(mock_client, "my-secret-bucket")


@patch("websnap.logic_s3.validate_s3_config_section")
@patch("websnap.logic_s3.terminate_program")
def test_write_urls_to_s3_value_error(mock_terminate, mock_validate_s3):
    """Test that a ValueError logs correctly and triggers termination logic."""
    parser = configparser.ConfigParser()
    parser.add_section("MySection")

    mock_validate_s3.side_effect = ValueError("Missing URL")

    log = MagicMock()
    client = MagicMock()

    write_urls_to_s3(parser, client, log, min_size_kb=1, early_exit=True)

    log.error.assert_called_once_with(
        "Validation failed for config section 'MySection': Missing URL"
    )
    mock_terminate.assert_called_once_with(True)


@patch("websnap.logic_s3.validate_s3_config_section")
@patch("websnap.logic_s3.validate_bucket_access")
@patch("websnap.logic_s3.terminate_program")
def test_write_urls_to_s3_bucket_access_error(
    mock_terminate, mock_bucket_access, mock_validate_s3
):
    """Test that a ValueError from bucket access triggers termination logic."""
    parser = configparser.ConfigParser()
    parser.add_section("Section2")

    mock_validate_s3.return_value = MagicMock(bucket="test-bucket")
    mock_bucket_access.side_effect = ValueError("Access Denied")

    log = MagicMock()

    write_urls_to_s3(parser, MagicMock(), log, min_size_kb=1, early_exit=False)

    log.error.assert_called_once_with(
        "Validation failed for config section 'Section2': Access Denied"
    )
    mock_terminate.assert_called_once_with(False)


@patch("websnap.logic_s3.validate_s3_config_section")
@patch("websnap.logic_s3.validate_bucket_access")
@patch("websnap.logic_s3.get_url_content")
@patch("websnap.logic_s3.terminate_program")
def test_write_urls_to_s3_skips_on_no_url_content(
    mock_terminate, mock_get_url, mock_bucket_access, mock_validate_s3
):
    """Test that the loop continues/skips when url_content is None."""
    parser = configparser.ConfigParser()
    parser.add_section("DownloadFailSection")

    mock_conf = MagicMock()
    mock_conf.url = "https://example.com"
    mock_conf.bucket = "my-bucket"
    mock_validate_s3.return_value = mock_conf
    mock_bucket_access.return_value = None
    mock_get_url.return_value = None

    log = MagicMock()
    client = MagicMock()

    write_urls_to_s3(parser, client, log, min_size_kb=1)

    mock_get_url.assert_called_once()
    assert log.info.call_count == 0
    mock_terminate.assert_not_called()


@patch("websnap.logic_s3.validate_s3_config_section")
@patch("websnap.logic_s3.validate_bucket_access")
@patch("websnap.logic_s3.get_url_content")
@patch("websnap.logic_s3.is_min_size_kb")
@patch("websnap.logic_s3.terminate_program")
def test_write_urls_to_s3_skips_on_min_size_failure(
    mock_terminate, mock_is_min_size, mock_get_url, mock_bucket_access, mock_validate_s3
):
    """Test that the loop skips to the next section if the file is too small."""
    parser = configparser.ConfigParser()
    parser.add_section("SmallFileSection")

    mock_conf = MagicMock()
    mock_conf.url = "https://example.com"
    mock_conf.bucket = "my-bucket"
    mock_validate_s3.return_value = mock_conf
    mock_bucket_access.return_value = None
    mock_get_url.return_value = b"tiny content"
    mock_is_min_size.return_value = False

    log = MagicMock()
    client = MagicMock()

    write_urls_to_s3(parser, client, log, min_size_kb=100)

    mock_is_min_size.assert_called_once()
    assert log.info.call_count == 0
    mock_terminate.assert_not_called()


@patch("websnap.logic_s3.validate_s3_config_section")
@patch("websnap.logic_s3.validate_bucket_access")
@patch("websnap.logic_s3.get_url_content")
@patch("websnap.logic_s3.is_min_size_kb")
@patch("websnap.logic_s3.handle_s3_client_error")
def test_write_urls_to_s3_skips_after_put_error(
    mock_handler, mock_min_size, mock_get_url, mock_bucket_access, mock_validate_s3
):
    """Verify that a PutObject failure in Section 1 doesn't stop Section 2."""
    parser = configparser.ConfigParser()
    parser.add_section("SectionFail")
    parser.add_section("SectionSuccess")

    mock_conf = MagicMock(bucket="my-bucket", key="data.bin", url="https://test.com")
    mock_validate_s3.return_value = mock_conf
    mock_bucket_access.return_value = None
    mock_get_url.return_value = b"valid content"
    mock_min_size.return_value = True

    client = MagicMock()

    err = ClientError({"Error": {"Code": "403", "Message": "Forbidden"}}, "PutObject")
    success_resp = {"ResponseMetadata": {"HTTPStatusCode": 200}}
    client.put_object.side_effect = [err, success_resp]

    log = MagicMock()

    write_urls_to_s3(parser, client, log, min_size_kb=1)

    assert client.put_object.call_count == 2
    mock_handler.assert_called_once_with(err, log, "SectionFail", False)
    log.info.assert_called_with(
        "Config section 'SectionSuccess': Successfully copied URL "
        "content to S3 object 'data.bin'"
    )


@patch("websnap.logic_s3.validate_s3_config_section")
@patch("websnap.logic_s3.validate_bucket_access")
@patch("websnap.logic_s3.get_url_content")
@patch("websnap.logic_s3.is_min_size_kb")
@patch("websnap.logic_s3.terminate_program")
def test_write_urls_to_s3_unexpected_status(
    mock_terminate, mock_is_min_size, mock_get_url, mock_bucket_access, mock_validate_s3
):
    """Test the else branch when put_object returns a non-200 status code."""
    parser = configparser.ConfigParser()
    parser.add_section("ErrorSection")

    mock_conf = MagicMock(bucket="my-bucket", key="data.txt", url="https://test.com")
    mock_validate_s3.return_value = mock_conf
    mock_bucket_access.return_value = None
    mock_get_url.return_value = b"some data"
    mock_is_min_size.return_value = True

    client = MagicMock()
    client.put_object.return_value = {"ResponseMetadata": {"HTTPStatusCode": 500}}

    log = MagicMock()

    write_urls_to_s3(parser, client, log, min_size_kb=1, early_exit=True)

    log.error.assert_called_once_with(
        "Config section 'ErrorSection': S3 client returned unexpected HTTP response 500"
    )
    mock_terminate.assert_called_once_with(True)
