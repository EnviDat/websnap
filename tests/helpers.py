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


def get_s3_config():
    return {
        "DEFAULT": {
            "endpoint_url": "https://dreamycloud.com",
            "aws_access_key_id": "1234567abcdefg",
            "aws_secret_access_key": "hijklmn1234567",
        },
        "pypi-websnap-s3": {
            "url": "https://pypi.org/pypi/websnap/json",
            "bucket": "pypi",
            "key": "output_s3.json",
        },
    }


def get_s3_config_invalid():
    return {
        "DEFAULT": {
            "endpoint_url": "not a real URL",
            "aws_access_key_id": "1234567abcdefg",
            "aws_secret_access_key": "hijklmn1234567",
        },
        "pypi-websnap-s3_invalid_key": {
            "url": "https://pypi.org/pypi/websnap/json",
            "bucket": "pypi",
            "key": "/output_s3.json",
        },
        "pypi-websnap-s3_invalid_key2": {
            "url": "https://pypi.org/pypi/websnap/json",
            "bucket": "pypi",
            "key": "output_s3json",
        },
        "no-bucket": {
            "url": "https://pypi.org/pypi/websnap/json",
            "key": "output_s3json",
        },
    }
