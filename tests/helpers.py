"""Helpers for tests."""

import json


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
