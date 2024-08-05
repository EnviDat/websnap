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

from websnap.validators import (
    validate_config_section,
    S3ConfigModel,
    validate_s3_config_section,
    ConfigSectionModel,
    S3ConfigSectionModel,
)


def terminate_program(early_exit: bool):
    """Terminates program execution if argument early_exit is True."""
    if early_exit:
        sys.exit("Error occurred: check logs for details")
    return


def get_url_content(
    url: str, section: str, log: logging.getLogger, early_exit: bool = False
) -> bytes | None:
    """
    Return content of response from HTTP GET request.
    If response status code is >= 400 then terminate program if argument early_exit
    is True, else return None.

    Args:
        url: URL to download.
        section: Name of config_templates section being processed.
        log: Logger object created with customized configuration file.
        early_exit: If True then terminates program immediately after error occurs.
            Default value is False.
            If False then only logs error and continues execution.
    """
    response = requests.get(url)

    if not response.ok:
        log.error(
            f"Config section '{section}': "
            f"URL returned unsuccessful HTTP response "
            f"status code {response.status_code}"
        )
        terminate_program(early_exit)
        return None

    return response.content


def is_min_size_kb(
    url_content: bytes,
    min_size_kb: int,
    section: str,
    log: logging.getLogger,
    early_exit: bool = False,
) -> bool | None:
    """
    Return True if url_content is greater than min_size_kb.
    Else return False or terminate program (if argument early_exit is True).

    Args:
        url_content: Content of response from HTTP request.
        min_size_kb: Minimum threshold in kilobytes that URL response content must be to
            write or upload file.
        section: Name of config_templates section being processed.
        log: Logger object created with customized configuration file.
        early_exit: If True then terminates program immediately after error occurs.
            Default value is False.
            If False then only logs error and continues execution.
    """
    data_kb = url_content.__sizeof__() / 1024

    if data_kb < min_size_kb:
        log.error(
            f"Config section '{section}': "
            f"URL response content in config_templates section {section} is less than "
            f"config_templates value 'min_size_kb' {min_size_kb}"
        )
        terminate_program(early_exit)
        return False

    return True


def write_urls_locally(
    conf_parser: configparser.ConfigParser,
    log: logging.getLogger,
    min_size_kb: int,
    early_exit: bool = False,
):
    """
    Download files hosted at URLS in config_templates and then write them to local
    machine.

    Args:
        conf_parser: ConfigParser object created from parsing configuration file.
        log: Logger object created with customized configuration file.
        min_size_kb: Minimum threshold in kilobytes that URL response content must be to
            write file.
        early_exit: If True then terminates program immediately after error occurs.
            Default value is False.
            If False then only logs error and continues execution.
    """
    for section in conf_parser.sections():

        try:
            conf = validate_config_section(conf_parser, section)
            if not isinstance(conf, ConfigSectionModel):
                log.error(f"Config section '{section}': {conf}")
                terminate_program(early_exit)
                continue

            if conf.directory and not os.path.isdir(conf.directory):
                log.error(
                    f"Config section '{section}': directory '{conf.directory}' "
                    f"does not exist"
                )
                terminate_program(early_exit)
                continue

            url_content = get_url_content(str(conf.url), section, log, early_exit)
            if not url_content:
                continue

            is_min_size = is_min_size_kb(
                url_content, min_size_kb, section, log, early_exit
            )
            if not is_min_size:
                continue

            if conf.directory:
                file_path = f"{conf.directory}/{conf.file_name}"
            else:
                file_path = f"{conf.file_name}"

            with open(file_path, "wb") as f:
                f.write(url_content)
                log.info(
                    f"Successfully downloaded URL content and wrote file locally in "
                    f"config_templates section: {section}"
                )

        except Exception as e:
            log.error(f"Config section '{section}', error(s): {e}")
            terminate_program(early_exit)

    return


def copy_s3_object(
    client: boto3.Session.client,
    conf: S3ConfigSectionModel,
    log: logging.getLogger,
    section: str,
    early_exit: bool = False,
):
    """
    Copy an object using S3 object config_templates.

    New object's name is constructed using the 'LastModified' timestamp of original
    object.

    Args:
        client : boto3.Session.client object created using configuration file values.
        conf: S3ConfigSectionModel object created from validated
            section of configuration file.
        log: Logger object created with customized configuration file.
        section: Name of config_templates section being processed.
        early_exit: If True then terminates program immediately after error occurs.
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
                f"S3 config_templates section '{section}': "
                f"Created new backup file '{key_copy}'"
            )
        else:
            log.error(
                f"S3 config_templates section '{section}': "
                f"Object backup attempt returned "
                f"unexpected HTTP response {status_code}"
            )
            terminate_program(early_exit)

    except ClientError as e:
        log.error(e)
        terminate_program(early_exit)

    return


def delete_s3_backup_object(
    client: boto3.Session.client,
    conf: S3ConfigSectionModel,
    log: logging.getLogger,
    section: str,
    backup_s3_count: int,
    early_exit: bool = False,
):
    """
    Delete a S3 backup object using S3 object config_templates.
    Only deletes object if backup objects exceed backup_s3_count.

    Only deletes object that corresponds to the file name in the configured key,
    allows for a timestamp in key created using copy_s3_object().

    Args:
        client : boto3.Session.client object created using configuration file values.
        conf: S3ConfigSectionModel object created from validated
            section of configuration file.
        log: Logger object created with customized configuration file.
        section: Name of config_templates section being processed.
        backup_s3_count: Copy and backup S3 objects in config_templates
            <backup_s3_count> times, remove object with the oldest last modified
            timestamp.
        early_exit: If True then terminates program immediately after error occurs.
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
                    f"S3 config_templates section '{section}': "
                    f"Deleted backup file '{delete_key}'"
                )
            else:
                log.error(
                    f"S3 config_templates section '{section}': Backup file delete "
                    f"attempt returned unexpected HTTP response {status_code}"
                )
                terminate_program(early_exit)

        else:
            log.info(
                f"S3 config_templates section '{section}': Current number of backup "
                f"files does not exceed backup S3 count {backup_s3_count}"
            )

    except ClientError as e:
        log.error(e)
        terminate_program(early_exit)

    return


def write_urls_to_s3(
    conf_parser: configparser.ConfigParser,
    conf_s3: S3ConfigModel,
    log: logging.getLogger,
    min_size_kb: int,
    backup_s3_count: int | None = None,
    early_exit: bool = False,
):
    """
    Download files hosted at URLS in config_templates and then upload them to S3 bucket.

    Args:
        conf_parser: ConfigParser object created from parsing configuration file.
        conf_s3: S3ConfigModel object created from validated configuration file.
        log: Logger object created with customized configuration file.
        min_size_kb: Minimum threshold in kilobytes that URL response content must be to
            upload file to S3 bucket.
        backup_s3_count: Copy and backup S3 objects in each config_templates section
            <backup_s3_count> times,
            remove object with the oldest last modified timestamp.
            If omitted then default value is None and objects are not copied or removed.
        early_exit: If True then terminates program immediately after error occurs.
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
                terminate_program(early_exit)
                continue

            url_content = get_url_content(str(conf.url), section, log, early_exit)
            if not url_content:
                continue

            is_min_size = is_min_size_kb(
                url_content, min_size_kb, section, log, early_exit
            )
            if not is_min_size:
                continue

            if backup_s3_count:
                copy_s3_object(client, conf, log, section, early_exit)
                delete_s3_backup_object(client, conf, log, section, backup_s3_count)

            response_s3 = client.put_object(
                Body=url_content, Bucket=conf.bucket, Key=conf.key
            )
            status_code = response_s3.get("ResponseMetadata", {}).get("HTTPStatusCode")

            if status_code == 200:
                log.info(
                    f"Config section '{section}': Successfully downloaded URL "
                    f"content and uploaded content to S3 object '{conf.key}'"
                )
            else:
                log.error(
                    f"Config section '{section}': S3 returned unexpected "
                    f"HTTP response {status_code}"
                )
                terminate_program(early_exit)

        except Exception as e:
            log.error(f"Config section '{section}', error(s): {e}")
            terminate_program(early_exit)

    return
