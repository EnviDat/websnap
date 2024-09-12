"""Tests for src/websnap/websnap.py"""

import json
import os
import pytest
import requests
from dotenv import load_dotenv

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

    load_dotenv()
    endpoint_url = os.getenv("ENDPOINT_URL")

    for section in s3_config_dict:

        if section == "DEFAULT":
            continue

        bucket = s3_config_dict[section]["bucket"]
        key = s3_config_dict[section]["key"]

        output_url = f"{endpoint_url}/{bucket}/{key}"

        response = requests.get(output_url, timeout=30)
        assert response.status_code == 200
