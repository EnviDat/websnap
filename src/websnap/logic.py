"""
Functions used to copy and write files retrieved from an API to a S3 bucket or a
local machine.
"""

import configparser
import logging
import os
import time
from math import ceil

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
    url: str,
    section: str,
    log: logging.getLogger,
    timeout: int = 32,
    early_exit: bool = False,
) -> bytes | None:
    """
    Return content of response from HTTP GET request.
    If response times out or response status code is >= 400 then terminate program if
    argument early_exit is True, else return None.

    Args:
        url: URL to download.
        section: Name of config section being processed.
        log: Logger object created with customized configuration file.
        timeout: Number of seconds to wait for response.
        early_exit: If True then terminates program immediately after error occurs.
            Default value is False.
            If False then only logs error and continues execution.
    """
    try:

        response = requests.get(url, timeout=timeout)

        if not response.ok:
            log.error(
                f"Config section '{section}': "
                f"URL returned unsuccessful HTTP response "
                f"status code {response.status_code}"
            )
            terminate_program(early_exit)
            return None

        return response.content

    except requests.exceptions.Timeout:  # pragma: no cover
        log.error(
            f"Config section '{section}': "
            f"URL timed out while waiting {timeout} seconds for response"
        )
        terminate_program(early_exit)
        return None


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
        section: Name of config section being processed.
        log: Logger object created with customized configuration file.
        early_exit: If True then terminates program immediately after error occurs.
            Default value is False.
            If False then only logs error and continues execution.
    """
    data_kb = url_content.__sizeof__() / 1024

    if data_kb < min_size_kb:
        log.error(
            f"Config section '{section}': "
            f"URL response content in config section {section} is less than "
            f"config value 'min_size_kb' {min_size_kb}"
        )
        terminate_program(early_exit)
        return False

    return True


def write_urls_locally(
    conf_parser: configparser.ConfigParser,
    log: logging.getLogger,
    min_size_kb: int,
    timeout: int = 32,
    early_exit: bool = False,
) -> None:
    """
    Download files hosted at URLS in config and then write them to local machine.

    Args:
        conf_parser: ConfigParser object created from parsing configuration file.
        log: Logger object created with customized configuration file.
        min_size_kb: Minimum threshold in kilobytes that URL response content must be to
            write file.
        timeout: Number of seconds to wait for response.
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

            if conf.directory and not os.path.isdir(conf.directory):  # pragma: no cover
                log.error(
                    f"Config section '{section}': directory '{conf.directory}' "
                    f"does not exist"
                )
                terminate_program(early_exit)
                continue

            url_content = get_url_content(
                str(conf.url), section, log, timeout, early_exit
            )
            if not url_content:  # pragma: no cover
                continue

            is_min_size = is_min_size_kb(
                url_content, min_size_kb, section, log, early_exit
            )
            if not is_min_size:  # pragma: no cover
                continue

            if conf.directory:
                file_path = f"{conf.directory}/{conf.file_name}"
            else:  # pragma: no cover
                file_path = f"{conf.file_name}"

            with open(file_path, "wb") as f:
                f.write(url_content)
                log.info(
                    f"Successfully downloaded URL content and wrote file locally in "
                    f"config section: {section}"
                )

        except Exception as e:  # pragma: no cover
            log.error(f"Config section '{section}', error(s): {e}")
            terminate_program(early_exit)

    return


def handle_s3_client_error(
    err: ClientError, log: logging.getLogger, section: str, early_exit: bool
) -> None:  # pragma: no cover
    """
    Handles and logs botocore.exceptions.ClientError returned by failed S3 client
    method call.

    Note: If HTTP status code 404 is returned with ClientError then logs warning but
    continues execution.

    Args:
        err: Client error returned from S3 client.
        log: Logger object created with customized configuration file.
        section: Name of config section being processed.
        early_exit: If True then terminates program immediately after error occurs.
            If False then only logs error and continues execution.
    """
    err_status_code = err.response.get("ResponseMetadata", {}).get("HTTPStatusCode")

    if err_status_code == 404:
        log.warning(f"Config section '{section}': Object not found")
    elif err_status_code == 403:
        log.error(
            f"Config section '{section}': Forbidden, check access credentials in config"
        )
        terminate_program(early_exit)
    else:
        log.error(err)
        terminate_program(early_exit)

    return


def copy_s3_object(
    client: boto3.Session.client,
    conf: S3ConfigSectionModel,
    log: logging.getLogger,
    section: str,
    early_exit: bool = False,
) -> None:
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
        early_exit: If True then terminates program immediately after error occurs.
            Default value is False.
            If False then only logs error and continues execution.
    """

    try:
        head_resp = client.head_object(Bucket=conf.bucket, Key=conf.key)

        last_modified = head_resp.get("LastModified")
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
                f"Config section '{section}': " f"Created new backup file '{key_copy}'"
            )
        else:  # pragma: no cover
            log.error(
                f"Config section '{section}': "
                f"Object backup attempt returned "
                f"unexpected HTTP response {status_code}"
            )
            terminate_program(early_exit)

    except ClientError as err:
        handle_s3_client_error(err, log, section, early_exit)

    return


def delete_s3_backup_object(
    client: boto3.Session.client,
    conf: S3ConfigSectionModel,
    log: logging.getLogger,
    section: str,
    backup_s3_count: int,
    early_exit: bool = False,
) -> None:
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
        backup_s3_count: Copy and backup S3 objects in config
            <backup_s3_count> times, remove object with the oldest last modified
            timestamp.
        early_exit: If True then terminates program immediately after error occurs.
            Default value is False.
            If False then only logs error and continues execution.
    """

    try:
        key_split = conf.key.rpartition("/")

        if not key_split[0]:
            response = client.list_objects_v2(  # pragma: no cover
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
                    f"Config section '{section}': "
                    f"Deleted backup file '{delete_key}'"
                )
            else:  # pragma: no cover
                log.error(
                    f"Config section '{section}': Backup file delete "
                    f"attempt returned unexpected HTTP response {status_code}"
                )
                terminate_program(early_exit)

        else:  # pragma: no cover
            log.info(
                f"Config section '{section}': Current number of backup "
                f"files does not exceed backup S3 count {backup_s3_count}"
            )

    except ClientError as err:
        handle_s3_client_error(err, log, section, early_exit)

    return


def write_urls_to_s3(
    conf_parser: configparser.ConfigParser,
    conf_s3: S3ConfigModel,
    log: logging.getLogger,
    min_size_kb: int,
    backup_s3_count: int | None = None,
    timeout: int = 32,
    early_exit: bool = False,
) -> None:
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
        timeout: Number of seconds to wait for response.
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
            if not isinstance(conf, S3ConfigSectionModel):  # pragma: no cover
                log.error(f"Config section '{section}': {conf}")
                terminate_program(early_exit)
                continue

            url_content = get_url_content(
                str(conf.url), section, log, timeout, early_exit
            )
            if not url_content:  # pragma: no cover
                continue

            is_min_size = is_min_size_kb(
                url_content, min_size_kb, section, log, early_exit
            )
            if not is_min_size:  # pragma: no cover
                continue

            if backup_s3_count:
                copy_s3_object(client, conf, log, section, early_exit)
                delete_s3_backup_object(
                    client, conf, log, section, backup_s3_count, early_exit
                )

            response_s3 = client.put_object(
                Body=url_content, Bucket=conf.bucket, Key=conf.key
            )
            status_code = response_s3.get("ResponseMetadata", {}).get("HTTPStatusCode")

            if status_code == 200:
                log.info(
                    f"Config section '{section}': Successfully copied URL "
                    f"content to S3 object '{conf.key}'"
                )
            else:  # pragma: no cover
                log.error(
                    f"Config section '{section}': S3 client returned unexpected "
                    f"HTTP response {status_code}"
                )
                terminate_program(early_exit)

        except ClientError as err:
            handle_s3_client_error(err, log, section, early_exit)

        except Exception as e:  # pragma: no cover
            log.error(f"Config section '{section}', error(s): {e}")
            terminate_program(early_exit)

    return


def sleep_until_next_iteration(
    sleep_minutes: int, start_time: float, log: logging.getLogger
) -> None:  # pragma: no cover
    """
    Sleep (delay execution) <sleep_minutes> minutes until next websnap iteration.

    Args:
        sleep_minutes: Number of minutes to sleep until executing next websnap
            iteration.
        start_time: Start time at beginning of websnap iteration,
            (time is specified as number of seconds since beginning of epoch.)
        log: Logger object created with customized configuration file.
    """
    sleep_secs = sleep_minutes * 60
    execution_secs = time.time() - start_time

    if sleep_secs > execution_secs:
        wait_seconds = int(sleep_secs - execution_secs)
        wait_minutes = wait_seconds / 60
        log.info(
            f"Sleeping {wait_seconds} seconds (about {ceil(wait_minutes)} minutes)"
            f" before next iteration..."
        )
        time.sleep(wait_seconds)

    return
