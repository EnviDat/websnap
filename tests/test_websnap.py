import json
import os

import pytest

from websnap import websnap


@pytest.fixture
def test_config(tmp_path):

    conf_dict = {
        "DEFAULT": {"min_size_kb": 1},
        "pypi-websnap": {
            "directory": str(tmp_path),
            "file_name": "pypi_websnap.json",
            "url": "https://pypi.org/pypi/websnap/json",
        },
    }

    config = f"{str(tmp_path)}/config.json"

    with open(config, "w") as f:
        f.write(json.dumps(conf_dict))

    return config, tmp_path


def test_websnap(test_config):

    config, tmp_path = test_config

    websnap(config=config, early_exit=True)

    output_path = f"{str(tmp_path)}/pypi_websnap.json"

    assert os.path.isfile(output_path)
    assert os.path.getsize(output_path) > 999

    with open(output_path, "r") as f:
        data = json.load(f)
        assert data["info"]["name"] == "websnap"
