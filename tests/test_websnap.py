"""Tests for src/websnap/websnap.py"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest
import requests

from websnap import websnap


def test_websnap(config_basic, config_min_size_kb, config_log, tmp_path):

    for conf in [config_basic, config_min_size_kb, config_log]:
        config_path, tmp_path, file_name = conf

        websnap(config=config_path, early_exit=True)

        output_path = f"{str(tmp_path)}/{file_name}"

        assert os.path.isfile(output_path)
        assert os.path.getsize(output_path) > 999

        with open(output_path, "r") as f:
            data = json.load(f)
            assert data["info"]["name"] == "websnap"


# This test only supports S3 configurations for buckets with public read access
def test_websnap_s3(s3_config):

    if not s3_config:
        pytest.skip("Option '--s3-config' is not set")

    endpoint_url = os.environ.get("ENDPOINT_URL")

    websnap(
        config=s3_config,
        s3_uploader=True,
        endpoint_url=endpoint_url,
        backup_s3_count=1,
        early_exit=True,
    )

    with open(s3_config, "r") as f:
        s3_config_dict = json.load(f)

    for section in s3_config_dict:
        if section == "DEFAULT":
            continue

        bucket = s3_config_dict[section]["bucket"]
        key = s3_config_dict[section]["key"]

        output_url = f"{endpoint_url}/{bucket}/{key}"

        response = requests.get(output_url, timeout=30)
        assert response.status_code == 200


@patch("websnap.websnap.sleep_until_next_iteration")
@patch("websnap.websnap.get_config_parser")
@patch("websnap.websnap.validate_log_config")
@patch("websnap.websnap.validate_min_size_kb")
@patch("websnap.websnap.get_custom_logger")
@patch("websnap.websnap.write_urls_locally")
def test_websnap_triggers_repeat_sleep(
    mock_write, mock_logger, mock_min_size, mock_val_log, mock_parser, mock_sleep
):
    """Test that repeat_minutes triggers the sleep function."""
    # Mocking parser to avoid actual file reads
    mock_parser.return_value = MagicMock(sections=lambda: ["Section1"])

    # Return a dummy logger
    log = MagicMock()
    mock_logger.return_value = log

    # Trigger: Use a side_effect to stop the infinite loop
    # Raise a StopIteration to exit the while loop
    mock_sleep.side_effect = StopIteration("Loop broken for testing")

    with pytest.raises(StopIteration, match="Loop broken for testing"):
        websnap(repeat_minutes=5)

    # Verify the sleep function was called with the correct minutes
    mock_sleep.assert_called_once()

    # Verify sleep function was called with the repeat_minutes value passed to websnap
    args, _ = mock_sleep.call_args
    assert args[0] == 5

    # Verify the log shows the iteration started
    log.info.assert_any_call("******* START WEBSNAP ITERATION *******")
