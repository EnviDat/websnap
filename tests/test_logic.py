"""Tests for src/websnap/logic.py"""

import pytest

from tests.helpers import get_section_config, write_json_config
from websnap.logger import get_custom_logger
from websnap.logic import terminate_program, get_url_content, is_min_size_kb


@pytest.fixture
def config_logic(tmp_path):

    error_config = {
        "error-response": {
            "directory": str(tmp_path),
            "file_name": "error_response.json",
            "url": "https://httpbin.org/status/400",
        },
    }

    file_name = "output_logic_valid.json"
    section_config = get_section_config(tmp_path, file_name)
    conf_dict = error_config | section_config

    config_path = f"{str(tmp_path)}/config_logic.json"
    write_json_config(config_path, conf_dict)

    return config_path, tmp_path, file_name


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
