"""Tests configuration with custom argument and shared websnap config fixtures."""

import json
import os

import pytest

from tests.helpers import (
    get_section_config,
    write_json_config,
    get_s3_config,
    get_s3_config_invalid,
)
from websnap.validators import get_config_parser, validate_log_config


def pytest_addoption(parser):
    parser.addoption(
        "--s3-config",
        action="store",
        default=None,
        help="Optional configuration file used to test websnap S3 functionality",
    )


def pytest_configure(config):

    s3_config = config.getoption("--s3-config")

    if s3_config is None:
        return

    if not os.path.exists(s3_config):
        raise pytest.UsageError(f"S3 config '{s3_config}' does not exist")

    with open(s3_config) as config_file:
        s3_config_dict = json.load(config_file)

    for section in s3_config_dict:
        if section == "DEFAULT":
            continue
        for setting in ["url", "bucket", "key"]:
            if setting not in s3_config_dict[section]:
                raise pytest.UsageError(
                    f"S3 config '{s3_config}' section '{section}' is missing required "
                    f"setting '{setting}'"
                )


@pytest.fixture
def s3_config(request):

    s3_config_path = request.config.getoption("--s3-config")

    if not s3_config_path:
        return None

    return s3_config_path


@pytest.fixture
def config_basic(tmp_path):
    file_name = "output_basic.json"
    section_config = get_section_config(tmp_path, file_name)
    config_path = f"{str(tmp_path)}/config_basic.json"

    write_json_config(config_path, section_config)

    return config_path, tmp_path, file_name


@pytest.fixture
def config_parser_basic(config_basic):
    return get_config_parser(config_basic[0])


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


@pytest.fixture
def config_parser_log(config_log):
    return get_config_parser(config_log[0])


@pytest.fixture
def log_config_model(config_parser_log):
    return validate_log_config(config_parser_log)


@pytest.fixture
def config_s3(tmp_path):
    s3_config = get_s3_config()
    config_path = f"{str(tmp_path)}/config_s3.json"
    write_json_config(config_path, s3_config)
    return config_path, tmp_path


@pytest.fixture
def config_parser_s3(config_s3):
    return get_config_parser(config_s3[0])


@pytest.fixture
def config_s3_invalid(tmp_path):
    s3_conf = get_s3_config_invalid()
    config_path = f"{str(tmp_path)}/config_s3_invalid.json"
    write_json_config(config_path, s3_conf)
    return config_path, tmp_path


@pytest.fixture
def config_parser_s3_invalid(config_s3_invalid):
    return get_config_parser(config_s3_invalid[0])
