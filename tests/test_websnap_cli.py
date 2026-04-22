"""Tests for src/websnap/websnap_cli.py"""
import pytest

from websnap.websnap_cli import main
import unittest.mock as mock


def test_websnap_cli(config_basic):
    # Mock sys.argv to simulate command line input
    test_args = ["websnap_cli", f"--config={config_basic[0]}", "--log-level=WARNING"]

    with mock.patch("sys.argv", test_args):
        try:
            main()
        except SystemExit as e:
            assert e.code == 0


def test_main_handles_value_error_cleanly():
    """
    Test that main catches a ValueError from websnap and exits with
    a clean 'ERROR: ...' message.
    """
    test_args = ["websnap_cli", "--config=config.ini"]

    # Patch sys.argv to simulate CLI call
    # and Patch websnap to trigger the error
    with mock.patch("sys.argv", test_args), \
            mock.patch("websnap.websnap") as mock_websnap:
        # Simulate a validation failure inside the core logic
        mock_websnap.side_effect = ValueError("Timeout must be positive")

        with pytest.raises(SystemExit) as excinfo:
            main()

        assert str(excinfo.value) == "ERROR: Timeout must be positive"


def test_main_handles_connection_error_cleanly():
    """
    Test that main catches a ConnectionError (e.g. S3 failure) and exits.
    """
    test_args = ["websnap_cli", "--s3-uploader"]

    with mock.patch("sys.argv", test_args), \
            mock.patch("websnap.websnap") as mock_websnap:
        mock_websnap.side_effect = ConnectionError("Could not reach S3")

        with pytest.raises(SystemExit) as excinfo:
            main()

        assert str(excinfo.value) == "ERROR: Could not reach S3"
