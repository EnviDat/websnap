"""
Functions used to copy and write files retrieved from an API to an S3 bucket.
"""

import configparser
import logging

import boto3
from botocore.config import Config
from botocore.exceptions import (
    ClientError,
    BotoCoreError,
    NoCredentialsError,
    EndpointConnectionError,
)

from websnap.logic import terminate_program, get_url_content, is_min_size_kb
from websnap.validators import (
    validate_s3_config_section,
    S3ConfigSectionModel,
)


def handle_s3_client_error(
    err: ClientError, log: logging.Logger, section: str, early_exit: bool
) -> None:
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
    log: logging.Logger,
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
                f"Config section '{section}': Created new backup file '{key_copy}'"
            )
        else:
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
    log: logging.Logger,
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

        objs = [obj for obj in response.get("Contents", [])]
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
                    f"Config section '{section}': Deleted backup file '{delete_key}'"
                )
            else:
                log.error(
                    f"Config section '{section}': Backup file delete "
                    f"attempt returned unexpected HTTP response {status_code}"
                )
                terminate_program(early_exit)

        else:
            log.info(
                f"Config section '{section}': Current number of backup "
                f"files does not exceed backup S3 count {backup_s3_count}"
            )

    except ClientError as err:
        handle_s3_client_error(err, log, section, early_exit)

    return


def create_s3_client(
    endpoint_url: str, profile_name: str = None
) -> boto3.Session.client:
    """
    Returns a validated Boto3 S3 client created using a shared AWS credentials file.

    To learn more see
    https://docs.aws.amazon.com/boto3/latest/guide/credentials.html#shared-credentials-file

    Args:
        endpoint_url: The complete URL to use for the constructed S3 client.
        profile_name: The name of a profile to use for S3 credentials file.
                      If not given, then the default profile is used.

    Raises:
        SystemExit: If the client could not be created.

    Returns:
        boto3.Session.client: Configured S3 client
    """
    try:
        session = (
            boto3.Session(profile_name=profile_name)
            if profile_name
            else boto3.Session()
        )

        client = session.client(
            service_name="s3",
            endpoint_url=endpoint_url,
            config=Config(
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
                connect_timeout=5,
                read_timeout=32,
                retries={"max_attempts": 3},
            ),
        )

    except (BotoCoreError, NoCredentialsError, EndpointConnectionError) as e:
        raise ConnectionError(f"Failed to create S3 client: {e}")

    return client


def validate_bucket_access(client: boto3.Session.client, bucket: str) -> None:
    """
    Raises ClientError if bucket does not exist or S3 client credentials are invalid.

    Args:
        client: Configured S3 client
        bucket: Name of S3 bucket that object will be written in.
    """
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError as e:
        raise ValueError(f"S3 credentials, endpoint and/or bucket are invalid: {e}")

    return


def write_urls_to_s3(
    conf_parser: configparser.ConfigParser,
    client: boto3.Session.client,
    log: logging.Logger,
    min_size_kb: int,
    backup_s3_count: int | None = None,
    timeout: int = 32,
    early_exit: bool = False,
) -> None:
    """
    Download files hosted at URLS in config and then upload them to S3 bucket.

    Args:
        conf_parser: ConfigParser object created from parsing configuration file.
        client: boto3.Session.client
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
    for section in conf_parser.sections():
        try:
            conf = validate_s3_config_section(conf_parser, section)
            validate_bucket_access(client, conf.bucket)
        except ValueError as e:
            log.error(f"Validation failed for config section '{section}': {e}")
            terminate_program(early_exit)
            continue

        url_content = get_url_content(str(conf.url), section, log, timeout, early_exit)
        if url_content is None:
            continue

        is_min_size = is_min_size_kb(url_content, min_size_kb, section, log, early_exit)
        if not is_min_size:
            continue

        if backup_s3_count:
            copy_s3_object(client, conf, log, section, early_exit)
            delete_s3_backup_object(
                client, conf, log, section, backup_s3_count, early_exit
            )

        try:
            response_s3 = client.put_object(
                Body=url_content, Bucket=conf.bucket, Key=conf.key
            )

            if (
                status_code := response_s3.get("ResponseMetadata", {}).get(
                    "HTTPStatusCode"
                )
            ) == 200:
                log.info(
                    f"Config section '{section}': Successfully copied URL "
                    f"content to S3 object '{conf.key}'"
                )
            else:
                log.error(
                    f"Config section '{section}': S3 client returned unexpected "
                    f"HTTP response {status_code}"
                )
                terminate_program(early_exit)

        except ClientError as err:
            handle_s3_client_error(err, log, section, early_exit)

    return
