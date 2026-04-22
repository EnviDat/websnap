"""Tests for src/websnap/websnap_cli.py"""

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
