"""
Function websnap() downloads files from URLs and uploads them to S3 bucket.
Also supports writing downloaded files to local machine.
"""

import configparser

from math import ceil
import time

from websnap.validators import (
    get_config_parser,
    validate_log_config,
    validate_s3_config,
    validate_min_size_kb,
    S3ConfigModel,
    LogConfigModel,
)
from websnap.logger import get_custom_logger
from websnap.logic import write_urls_locally, write_urls_to_s3

__all__ = ["websnap"]

LOGGER_NAME = "websnap"


def websnap(
    config: str = "config.ini",
    log_level: str = "INFO",
    file_logs: bool = False,
    s3_uploader: bool = False,
    backup_s3_count: int | None = None,
    timeout: int = 32,
    early_exit: bool = False,
    repeat_minutes: int | None = None,
) -> None | Exception:
    """
    Copies files hosted at URLs in config and then uploads them
    to S3 bucket or local machine.
    Optionally customize rotating logs.
    Optionally repeat websnap file processing iteration.

    Args:
        config: Path to ini config file.
        log_level: Level to use for logging.
        file_logs: If True then implements rotating file logs.
        s3_uploader: If True then uploads files to S3 bucket.
        backup_s3_count: Copy and backup S3 objects in each config section
            <backup_s3_count> times,
            remove object with the oldest last modified timestamp.
            If omitted then default value is None and objects are not copied.
        timeout: Number of seconds to wait for response for each HTTP request.
        early_exit: If True then terminates program immediately after error occurs.
            Default value is False.
            If False then only logs error and continues execution.
        repeat_minutes: Run websnap continuously every <repeat> minutes, if omitted
            then default value is None and websnap will not repeat.
    """
    # Validate log settings in config and setup log
    try:
        conf_parser = get_config_parser(config)
        if not isinstance(conf_parser, configparser.ConfigParser):
            raise Exception(conf_parser)

        conf_log = validate_log_config(conf_parser)
        if not isinstance(conf_log, LogConfigModel):
            raise Exception(conf_log)

        log = get_custom_logger(
            name=LOGGER_NAME,
            level=log_level,
            file_logs=file_logs,
            config=conf_log,
        )
    except Exception as e:
        raise Exception(e)

    # Validate min_size_kb in config
    min_size_kb = validate_min_size_kb(conf_parser)
    if not isinstance(min_size_kb, int):
        raise Exception(min_size_kb)

    # Download and write URL files
    is_repeat = True
    while is_repeat:

        # Do not repeat iteration if repeat_minutes is None
        is_repeat = repeat_minutes is not None

        start_time = time.time()

        log.info("******* STARTED WEBSNAP ITERATION *******")
        log.info(
            f"Read config file: '{config}', it has sections: "
            f"{conf_parser.sections()}"
        )

        if s3_uploader:
            conf_s3 = validate_s3_config(conf_parser)
            if not isinstance(conf_s3, S3ConfigModel):
                raise Exception(conf_s3)
            write_urls_to_s3(
                conf_parser,
                conf_s3,
                log,
                min_size_kb,
                backup_s3_count,
                timeout,
                early_exit,
            )
        else:
            write_urls_locally(conf_parser, log, min_size_kb, timeout, early_exit)

        log.info("Finished websnap iteration")
        exec_time = int(time.time() - start_time)

        if is_repeat:
            interval_seconds = int(repeat_minutes) * 60
            if interval_seconds > exec_time:
                wait_seconds = interval_seconds - exec_time
                wait_minutes = wait_seconds / 60
                log.info(
                    f"Sleeping {wait_seconds} seconds (about {ceil(wait_minutes)} "
                    f"minutes) before next iteration..."
                )
                time.sleep(wait_seconds)

    return
