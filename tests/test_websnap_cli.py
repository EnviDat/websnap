"""Tests for src/websnap/websnap_cli.py"""

import subprocess


def test_websnap_cli(config_basic):

    result_pass = subprocess.run(
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
    assert result_pass.returncode == 0

    result_fail = subprocess.run(
        [
            "websnap_cli",
            "--timeout=not_a_number",
        ],
        capture_output=True,
        text=True,
    )
    assert result_fail.returncode != 0
