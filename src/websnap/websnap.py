"""
Supports downloading files hosted at URLs in config and then uploading
them to S3 bucket or local machine.

TODO finish WIP
TODO test using as a function from a package
TODO test passing logger and setting up default loggers
TODO write one with date and one with generic name, delete the old ones
"""

import time

from src.websnap.validators import (
    get_config_parser,
    validate_log_config,
    validate_s3_config,
    validate_min_size_kb,
    S3ConfigModel,
)
from src.websnap.logger import get_custom_logger
from src.websnap.logic import write_urls_locally, write_urls_to_s3

__all__ = ["websnap"]

LOGGER_NAME = "websnap"


# TODO add validation for section config and add s3_config.ini config
# TODO add argument to CLI:  has_s3_uploader: bool = False
# TODO test with different paths to config
# TODO add argument: backup_s3_count: int | None = None (and add to CLI)
def websnap(
    config: str = "./config/config.ini",
    log_level: str = "INFO",
    has_file_logs: bool = False,
    has_s3_uploader: bool = False,
    repeat_interval: int | None = None,
):
    """
    Download files hosted at URLs in config and then uploads them
    to S3 bucket or local machine.
    Optionally customize rotating logs.
    Optionally repeat websnap file processing iteration.

    Args:
        config: Path to ini config file.
        log_level: Level to use for logging.
        has_file_logs: If True then implements rotating file logs.
        has_s3_uploader: If True then uploads files to S3 bucket.
        repeat_interval: Run websnap continuously every <repeat> minutes, if omitted
            then default value is None and websnap will not repeat.
    """
    # Validate log settings in config
    try:
        conf_parser = get_config_parser(config)
        conf_log = validate_log_config(conf_parser)
        log = get_custom_logger(
            name=LOGGER_NAME,
            level=log_level,
            has_file_logs=has_file_logs,
            config=conf_log,
        )
    except Exception as e:
        print(f"ERROR: {e}")
        return

    # Validate min_size_kb in config
    try:
        min_size_kb = validate_min_size_kb(conf_parser)
        if not isinstance(min_size_kb, int):
            raise Exception(min_size_kb)
    except Exception as e:
        log.error(e)
        return

    # Download and write URL files
    is_repeat = True
    while is_repeat:

        # Do not repeat iteration if repeat_interval is None
        is_repeat = repeat_interval is not None

        start_time = time.time()

        log.info("******* STARTED WEBSNAP ITERATION *******")
        log.info(
            f"Read config file: {config}, it has sections: {conf_parser.sections()}"
        )

        # TODO WIP start dev here
        # TODO write log.write_urls_s3(), include backup_s3_count argument
        if has_s3_uploader:
            try:
                conf_s3 = validate_s3_config(conf_parser)
                if not isinstance(conf_s3, S3ConfigModel):
                    raise Exception(conf_s3)
                write_urls_to_s3(conf_parser, conf_s3, log, min_size_kb)
            except Exception as e:
                log.error(e)
                return
        else:
            write_urls_locally(conf_parser, log, min_size_kb)

        log.info("Finished websnap iteration")
        exec_time = int(time.time() - start_time)

        if is_repeat:
            interval_seconds = int(repeat_interval) * 60
            if interval_seconds > exec_time:
                wait_time = interval_seconds - exec_time
                log.info(f"Sleeping {wait_time} seconds before next iteration...")
                time.sleep(wait_time)

    return
