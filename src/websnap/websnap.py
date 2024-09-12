"""
Function websnap() downloads files from URLs and uploads them to S3 bucket.
Also supports writing downloaded files to local machine.
"""

import logging
import time

from websnap.constants import TIMEOUT
from websnap.validators import (
    get_config_parser,
    validate_log_config,
    validate_s3_config,
    validate_min_size_kb,
    validate_positive_int_args,
)
from websnap.logger import get_custom_logger
from websnap.logic import (
    write_urls_locally,
    write_urls_to_s3,
    sleep_until_next_iteration,
)

__all__ = ["websnap"]

LOGGER_NAME = "websnap"


def websnap(
    config: str = "config.ini",
    log_level: str = "INFO",
    file_logs: bool = False,
    s3_uploader: bool = False,
    backup_s3_count: int | None = None,
    timeout: int = TIMEOUT,
    early_exit: bool = False,
    repeat_minutes: int | None = None,
    section_config: str | None = None,
) -> None:
    """
    Copies files hosted at URLs in config and then uploads them
    to S3 bucket or local machine.

    Args:
        config: Path to .ini or .json configuration file.
        log_level: Level to use for logging.
        file_logs: If True then implements rotating file logs.
        s3_uploader: If True then uploads files to S3 bucket.
        backup_s3_count: Copy and backup S3 objects in each config section
            <backup_s3_count> times,
            remove object with the oldest last modified timestamp.
            If integer passed then it must be a positive integer.
            If omitted then default value is None and objects are not copied.
        timeout: Number of seconds to wait for response for each HTTP request.
            If integer passed then it must be a positive integer.
        early_exit: If True then terminates program immediately after error occurs.
            Default value is False.
            If False then only logs error and continues execution.
        repeat_minutes: Run websnap continuously every <repeat> minutes
               If integer passed then it must be a positive integer.
               If omitted then default value is None and websnap will not repeat.
        section_config: File or URL to obtain additional configuration sections.
                If omitted then default value is None and only config specified in
                'config' argument is used.
                Cannot be used to assign DEFAULT values in the config (DEFAULT
                values must be assigned in config specified by 'config' argument).
                Currently only supports JSON config and can only be used if 'config'
                argument is also a JSON file.
                Duplicate sections will overwrite values with the same section
                passed in the `config` argument.
    """
    # Validate integer arguments
    try:
        validate_positive_int_args(timeout, backup_s3_count, repeat_minutes)
    except Exception as e:
        raise e

    # Validate configuration
    try:
        conf_parser = get_config_parser(config, section_config, timeout)
        conf_log = validate_log_config(conf_parser)
        min_size_kb = validate_min_size_kb(conf_parser)
    except Exception as e:
        raise e

    # Validate custom log
    log = get_custom_logger(
        name=LOGGER_NAME,
        level=log_level,
        file_logs=file_logs,
        config=conf_log,
    )
    if not isinstance(log, logging.Logger):
        raise Exception(log)

    # Copy URL files and write to S3 bucket or local machine
    is_repeat = True
    while is_repeat:

        # Do not repeat iteration if repeat_minutes is None
        is_repeat = repeat_minutes is not None

        start_time = time.time()

        log.info("******* START WEBSNAP ITERATION *******")
        log.info(
            f"Read config file: '{config}', it has sections: "
            f"{conf_parser.sections()}"
        )

        if s3_uploader:
            try:
                conf_s3 = validate_s3_config()
            except Exception as e:
                raise e
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

        if is_repeat:  # pragma: no cover
            sleep_until_next_iteration(repeat_minutes, start_time, log)

    return
