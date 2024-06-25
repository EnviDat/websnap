"""
Supporting functions used to download and write files hosted
at URLs to S3 bucket or local machine.
"""

import configparser
import logging
import os
import requests
import boto3
from botocore.exceptions import ClientError

from src.websnap.validators import (
    validate_config_section,
    S3ConfigModel,
    validate_s3_config_section,
    ConfigSectionModel,
    S3ConfigSectionModel,
)


# TODO test with CLI
def write_urls_locally(
    conf_parser: configparser.ConfigParser, log: logging.getLogger, min_size_kb: int
) -> None | Exception:
    """
    Download files hosted at URLS in config and then upload them to local machine.

    Args:
        conf_parser: ConfigParser object created from parsing configuration file.
        log: Logger object created with customized configuration file.
        min_size_kb: Minimum threshold in kilobytes that URL response content must be to
            write file.
    """
    for section in conf_parser.sections():

        try:
            conf = validate_config_section(conf_parser, section)
            if not isinstance(conf, ConfigSectionModel):
                log.error(f"Config section '{section}': {conf}")
                continue

            if not os.path.isdir(conf.directory):
                log.error(
                    f"Config section '{section}': directory '{conf.directory}' "
                    f"does not exist"
                )
                continue

            url = str(conf.url)
            response = requests.get(url)

            if not response.ok:
                log.error(
                    f"Config section '{section}': "
                    f"URL returned unsuccessful HTTP response "
                    f"status code {response.status_code}"
                )
                continue

            data = response.content

            # TODO test
            data_kb = data.__sizeof__() / 1024
            if data_kb < min_size_kb:
                log.error(
                    f"Config section '{section}': "
                    f"URL response content in config section {section} is less than "
                    f"config value 'min_size_kb' {min_size_kb}"
                )
                continue

            file_path = f"{conf.directory}/{conf.file_name}"
            with open(file_path, "wb") as f:
                f.write(data)
                log.info(
                    f"Successfully downloaded URL content and wrote file in "
                    f"config section: {section}"
                )

        except Exception as e:
            log.error(f"Config section '{section}', error(s): {e}")

    return


# TODO finish WIP, start dev here
# TODO test with slash before config key values, may need to add additional validation
# TODO implement backup_s3_count argument
# TODO test with CLI
# TODO review function
def write_urls_to_s3(
    conf_parser: configparser.ConfigParser,
    conf_s3: S3ConfigModel,
    log: logging.getLogger,
    min_size_kb: int,
) -> None | Exception:
    """
    Download files hosted at URLS in config and then upload them to S3 bucket.

    Args:
        conf_parser: ConfigParser object created from parsing configuration file.
        conf_s3: S3ConfigModel object created from validated configuration file.
        log: Logger object created with customized configuration file.
        min_size_kb: Minimum threshold in kilobytes that URL response content must be to
            upload file to S3 bucket.
    """
    session = boto3.Session(
        aws_access_key_id=conf_s3.aws_access_key_id,
        aws_secret_access_key=conf_s3.aws_secret_access_key,
    )

    client = session.client(service_name="s3", endpoint_url=str(conf_s3.endpoint_url))

    for section in conf_parser.sections():

        try:
            conf = validate_s3_config_section(conf_parser, section)
            if not isinstance(conf, S3ConfigSectionModel):
                log.error(f"Config section '{section}': {conf}")
                continue

            url = str(conf.url)
            response = requests.get(url)

            if not response.ok:
                log.error(
                    f"Config section '{section}': "
                    f"URL returned unsuccessful HTTP response "
                    f"status code {response.status_code}"
                )
                continue

            data = response.content

            # TODO test
            data_kb = data.__sizeof__() / 1024
            if data_kb < min_size_kb:
                log.error(
                    f"Config section '{section}': "
                    f"URL response content in config section {section} is less than "
                    f"config value 'min_size_kb' {min_size_kb}"
                )
                continue

            # TODO WIP
            # TODO add condition backup_s3_count for function
            # backup_s3_objects(client, section, conf, data, log)

            response_s3 = client.put_object(Body=data, Bucket=conf.bucket, Key=conf.key)

            status_code = response_s3.get("ResponseMetadata", {}).get("HTTPStatusCode")

            if status_code == 200:
                log.info(
                    f"Successfully downloaded URL content and uploaded file to S3 "
                    f"bucket in config section: {section}"
                )
            else:
                log.error(
                    f"Config section '{section}': S3 returned unexpected "
                    f"HTTP response {status_code}"
                )

        except Exception as e:
            log.error(f"Config section '{section}', error(s): {e}")

    return


# TODO move function up
# TODO WIP finish
# TODO remove print statements
# TODO remove unused arguments
def backup_s3_objects(
    client: boto3.Session.client,
    section: str,
    conf: S3ConfigSectionModel,
    data: bytes,
    log: logging.getLogger,
):
    """
    Backup up and delete old copies of an object in the same bucket subdirectory.

    Args:
        client : boto3.Session.client object created using configuration file values.
        section: Name of current config section being processed.
        conf: S3ConfigSctionModel object created from validated
            section of configuration file.
        data: URL (from config) HTTP response content in bytes.
        log: Logger object created with customized configuration file.
    """

    prefix = conf.key.rpartition("/")[0]
    prefix = f"{prefix}/"

    try:
        # Get object with configured key
        obj = client.head_object(Bucket=conf.bucket, Key=conf.key)
        # print(obj)  # TODO remove

        last_modified = obj.get("LastModified")
        # print(last_modified)
        # print(type(last_modified))

        format_date = "%Y-%m-%d_%H-%M-%S"
        datetime_str = last_modified.strftime(format_date)
        # print(datetime_str)

        key_split = conf.key.rpartition(".")
        key_copy = f"{key_split[0]}_{datetime_str}{key_split[1]}{key_split[2]}"
        print(key_copy)

        # TODO debug
        # Copy object
        # obj_copy = client.copy_object(
        #     Bucket=conf.bucket,
        #     CopySource=conf.key,
        #     Key=key_copy,
        # )
        #
        # # TODO handle response
        # print(obj_copy)

    except ClientError as e:
        log.warning(e)
