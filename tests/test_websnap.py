"""Tests for src/websnap/websnap.py"""

import json
import logging
import os
import pytest

from websnap import websnap


def write_json_config(config_path: str, conf_dict: dict):
    with open(config_path, "w") as f:
        f.write(json.dumps(conf_dict))


def get_section_config(tmp_path, file_name: str):
    return {
        "pypi-websnap": {
            "directory": str(tmp_path),
            "file_name": file_name,
            "url": "https://pypi.org/pypi/websnap/json",
        },
    }


@pytest.fixture
def config_basic(tmp_path):

    file_name = "output_basic.json"
    section_config = get_section_config(tmp_path, file_name)
    config_path = f"{str(tmp_path)}/config_basic.json"

    write_json_config(config_path, section_config)

    return config_path, tmp_path, file_name


@pytest.fixture
def config_min_size_kb(tmp_path):

    default_config = {"DEFAULT": {"min_size_kb": 1}}
    file_name = "output_min_size_kb.json"
    section_config = get_section_config(tmp_path, file_name)
    conf_dict = default_config | section_config

    config_path = f"{str(tmp_path)}/config_min_size_kb.json"
    write_json_config(config_path, conf_dict)

    return config_path, tmp_path, file_name


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


def test_websnap(config_basic, config_min_size_kb, config_log):

    for conf in [config_basic, config_min_size_kb, config_log]:

        config_path, tmp_path, file_name = conf

        websnap(config=config_path, early_exit=True)

        output_path = f"{str(tmp_path)}/{file_name}"

        assert os.path.isfile(output_path)
        assert os.path.getsize(output_path) > 999

        with open(output_path, "r") as f:
            data = json.load(f)
            assert data["info"]["name"] == "websnap"
