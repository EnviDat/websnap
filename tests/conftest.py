"""Tests configuration with shared fixture."""

import pytest

from tests.helpers import get_section_config, write_json_config


@pytest.fixture
def config_log(tmp_path):

    log_config = {
        "DEFAULT": {
            "log_when": "midnight",
            "log_interval": 2,
            "log_backup_count": 2,
        }
    }
    file_name = "output_log.json"
    section_config = get_section_config(tmp_path, file_name)
    conf_dict = log_config | section_config

    config_path = f"{str(tmp_path)}/config_log.json"
    write_json_config(config_path, conf_dict)

    return config_path, tmp_path, file_name
