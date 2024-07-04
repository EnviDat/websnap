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
import sys

from src.websnap.validators import (
    validate_config_section,
    S3ConfigModel,
    validate_s3_config_section,
    ConfigSectionModel,
    S3ConfigSectionModel,
)


def terminate_program(has_early_exit: bool):
    """Terminates program execution if argument has_early_exit is True."""
    if has_early_exit:
        sys.exit("Error occured: check logs for details")
    return


def write_urls_locally(
    conf_parser: configparser.ConfigParser,
    log: logging.getLogger,
    min_size_kb: int,
    has_early_exit: bool = False,
):
    """
    Download files hosted at URLS in config and then upload them to local machine.

    Args:
        conf_parser: ConfigParser object created from parsing configuration file.
        log: Logger object created with customized configuration file.
        min_size_kb: Minimum threshold in kilobytes that URL response content must be to
            write file.
        has_early_exit: If True then terminates program immediately after error occurs.
            Default value is False.
            If False then only logs error and continues execution.
    """
    for section in conf_parser.sections():

        try:
            conf = validate_config_section(conf_parser, section)
            if not isinstance(conf, ConfigSectionModel):
                log.error(f"Config section '{section}': {conf}")
                terminate_program(has_early_exit)
                continue

            if conf.directory and not os.path.isdir(conf.directory):
                log.error(
                    f"Config section '{section}': directory '{conf.directory}' "
                    f"does not exist"
                )
                terminate_program(has_early_exit)
                continue

            url = str(conf.url)
            response = requests.get(url)

            if not response.ok:
                log.error(
                    f"Config section '{section}': "
                    f"URL returned unsuccessful HTTP response "
                    f"status code {response.status_code}"
                )
                terminate_program(has_early_exit)
                continue

            data = response.content

            data_kb = data.__sizeof__() / 1024
            if data_kb < min_size_kb:
                log.error(
                    f"Config section '{section}': "
                    f"URL response content in config section {section} is less than "
                    f"config value 'min_size_kb' {min_size_kb}"
                )
                terminate_program(has_early_exit)
                continue

            if conf.directory:
                file_path = f"{conf.directory}/{conf.file_name}"
            else:
                file_path = f"{conf.file_name}"

            with open(file_path, "wb") as f:
                f.write(data)
                log.info(
                    f"Successfully downloaded URL content and wrote file in "
                    f"config section: {section}"
                )

        except Exception as e:
            log.error(f"Config section '{section}', error(s): {e}")
            terminate_program(has_early_exit)

    return


def copy_s3_object(
    client: boto3.Session.client,
    conf: S3ConfigSectionModel,
    log: logging.getLogger,
    section: str,
    has_early_exit: bool = False,
):
    """
    Copy an object using S3 object config.

    New object's name is constructed using the 'LastModified' timestamp of original
    object.

    Args:
        client : boto3.Session.client object created using configuration file values.
        conf: S3ConfigSectionModel object created from validated
            section of configuration file.
        log: Logger object created with customized configuration file.
        section: Name of config section being processed.
        has_early_exit: If True then terminates program immediately after error occurs.
            Default value is False.
            If False then only logs error and continues execution.
    """

    try:
        obj = client.head_object(Bucket=conf.bucket, Key=conf.key)

        last_modified = obj.get("LastModified")
        format_date = "%Y-%m-%d_%H-%M-%S"
        datetime_str = last_modified.strftime(format_date)
        key_split = conf.key.rpartition(".")
        key_copy = f"{key_split[0]}_{datetime_str}{key_split[1]}{key_split[2]}"

        response = client.copy_object(
            CopySource={"Bucket": conf.bucket, "Key": conf.key},
            Bucket=conf.bucket,
            Key=key_copy,
        )

        status_code = response.get("ResponseMetadata", {}).get("HTTPStatusCode")

        if status_code == 200:
            log.info(
                f"S3 config section '{section}': Created new backup file '{key_copy}'"
            )
        else:
            log.error(
                f"S3 config section '{section}': Object backup attempt returned "
                f"unexpected HTTP response {status_code}"
            )
            terminate_program(has_early_exit)

    except ClientError as e:
        log.error(e)
        terminate_program(has_early_exit)

    return


def delete_s3_backup_object(
    client: boto3.Session.client,
    conf: S3ConfigSectionModel,
    log: logging.getLogger,
    section: str,
    backup_s3_count: int,
    has_early_exit: bool = False,
):
    """
    Delete a S3 backup object using S3 object config.
    Only deletes object if backup objects exceed backup_s3_count.

    Only deletes object that corresponds to the file name in the configured key,
    allows for a timestamp in key created using copy_s3_object().

    Args:
        client : boto3.Session.client object created using configuration file values.
        conf: S3ConfigSectionModel object created from validated
            section of configuration file.
        log: Logger object created with customized configuration file.
        section: Name of config section being processed.
        backup_s3_count: Copy and backup S3 objects in config <backup_s3_count> times,
            remove object with the oldest last modified timestamp.
        has_early_exit: If True then terminates program immediately after error occurs.
            Default value is False.
            If False then only logs error and continues execution.
    """

    try:
        key_split = conf.key.rpartition("/")

        if not key_split[0]:
            response = client.list_objects_v2(
                Bucket=conf.bucket,
            )
        else:
            response = client.list_objects_v2(
                Bucket=conf.bucket, Prefix=f"{key_split[0]}{key_split[1]}"
            )

        file_split = key_split[2].rpartition(".")
        file_start = f"{file_split[0]}_"
        file_end = f"{file_split[1]}{file_split[2]}"

        objs = [obj for obj in response.get("Contents")]
        match_objs = []

        for obj in objs:
            ky = obj.get("Key")
            ky_split = ky.rpartition("/")
            ky_file = ky_split[2]
            if ky_file.startswith(file_start) and ky_file.endswith(file_end):
                match_objs.append(obj)

        sorted_objs = sorted(match_objs, key=lambda x: x["LastModified"])

        if len(sorted_objs) > backup_s3_count:

            obj_oldest = sorted_objs[0]
            delete_key = obj_oldest.get("Key")

            resp = client.delete_object(Bucket=conf.bucket, Key=delete_key)

            status_code = resp.get("ResponseMetadata", {}).get("HTTPStatusCode")

            if status_code == 204:
                log.info(
                    f"S3 config section '{section}': "
                    f"Deleted backup file '{delete_key}'"
                )
            else:
                log.error(
                    f"S3 config section '{section}': Backup file delete attempt "
                    f"returned unexpected HTTP response {status_code}"
                )
                terminate_program(has_early_exit)

        else:
            log.info(
                f"S3 config section '{section}': Current number of backup files "
                f"does not exceed backup S3 count {backup_s3_count}"
            )

    except ClientError as e:
        log.error(e)
        terminate_program(has_early_exit)

    return


def write_urls_to_s3(
    conf_parser: configparser.ConfigParser,
    conf_s3: S3ConfigModel,
    log: logging.getLogger,
    min_size_kb: int,
    backup_s3_count: int | None = None,
    has_early_exit: bool = False,
):
    """
    Download files hosted at URLS in config and then upload them to S3 bucket.

    Args:
        conf_parser: ConfigParser object created from parsing configuration file.
        conf_s3: S3ConfigModel object created from validated configuration file.
        log: Logger object created with customized configuration file.
        min_size_kb: Minimum threshold in kilobytes that URL response content must be to
            upload file to S3 bucket.
        backup_s3_count: Copy and backup S3 objects in each config section
            <backup_s3_count> times,
            remove object with the oldest last modified timestamp.
            If omitted then default value is None and objects are not copied or removed.
        has_early_exit: If True then terminates program immediately after error occurs.
            Default value is False.
            If False then only logs error and continues execution.
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
                terminate_program(has_early_exit)
                continue

            url = str(conf.url)
            response = requests.get(url)

            if not response.ok:
                log.error(
                    f"S3 config section '{section}': "
                    f"URL returned unsuccessful HTTP response "
                    f"status code {response.status_code}"
                )
                terminate_program(has_early_exit)
                continue

            data = response.content

            data_kb = data.__sizeof__() / 1024
            if data_kb < min_size_kb:
                log.error(
                    f"S3 config section '{section}': "
                    f"URL response content in config section {section} is less than "
                    f"config value 'min_size_kb' {min_size_kb}"
                )
                terminate_program(has_early_exit)
                continue

            if backup_s3_count:
                copy_s3_object(client, conf, log, section, has_early_exit)
                delete_s3_backup_object(client, conf, log, section, backup_s3_count)

            response_s3 = client.put_object(Body=data, Bucket=conf.bucket, Key=conf.key)
            status_code = response_s3.get("ResponseMetadata", {}).get("HTTPStatusCode")

            if status_code == 200:
                log.info(
                    f"S3 config section '{section}': Successfully downloaded URL "
                    f"content and uploaded file '{conf.key}'"
                )
            else:
                log.error(
                    f"S3 config section '{section}': S3 returned unexpected "
                    f"HTTP response {status_code}"
                )
                terminate_program(has_early_exit)

        except Exception as e:
            log.error(f"Config section '{section}', error(s): {e}")
            terminate_program(has_early_exit)

    return
