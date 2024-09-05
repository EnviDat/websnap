"""Tests for src/websnap/websnap_cli.py"""

import subprocess


def test_websnap_cli(config_basic):

    result = subprocess.run(
        [
            "websnap_cli",
            f"--config={config_basic[0]}",
            "--log_level=WARNING",
            "--file_logs",
            "--timeout=30",
            "--early_exit",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
