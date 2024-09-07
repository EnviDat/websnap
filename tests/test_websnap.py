"""Tests for src/websnap/websnap.py"""

import json
import os
import pytest
import requests

from websnap import websnap


def test_websnap(config_basic, config_min_size_kb, config_log, tmp_path):

    for conf in [config_basic, config_min_size_kb, config_log]:

        config_path, tmp_path, file_name = conf

        websnap(config=config_path, early_exit=True)

        output_path = f"{str(tmp_path)}/{file_name}"

        assert os.path.isfile(output_path)
        assert os.path.getsize(output_path) > 999

        with open(output_path, "r") as f:
            data = json.load(f)
            assert data["info"]["name"] == "websnap"


# This test only supports S3 configurations for buckets with public read access
def test_websnap_s3(s3_config):

    if not s3_config:
        pytest.skip("Option '--s3-config' is not set")

    websnap(config=s3_config, s3_uploader=True, backup_s3_count=1, early_exit=True)

    with open(s3_config, "r") as f:
        s3_config_dict = json.load(f)

    endpoint_url = s3_config_dict["DEFAULT"]["endpoint_url"]

    for section in s3_config_dict:

        if section == "DEFAULT":
            continue

        bucket = s3_config_dict[section]["bucket"]
        key = s3_config_dict[section]["key"]

        output_url = f"{endpoint_url}/{bucket}/{key}"

        response = requests.get(output_url, timeout=30)
        assert response.status_code == 200


@pytest.mark.parametrize(
    "backup_s3_count, timeout, repeat_minutes", [(0, 1, 1), (1, 0, 1), (1, 1, 0)]
)
def test_websnap_args_positive_integer(backup_s3_count, timeout, repeat_minutes):
    with pytest.raises(Exception):
        websnap(
            backup_s3_count=backup_s3_count,
            timeout=timeout,
            repeat_minutes=repeat_minutes,
        )


def test_websnap_s3_config_invalid(config_s3_invalid):
    with pytest.raises(Exception):
        conf = config_s3_invalid[0]
        websnap(config=conf, s3_uploader=True)
