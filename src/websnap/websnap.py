"""
Supports downloading files hosted at URLs in config and then uploading
them to S3 bucket or local machine.

TODO finish WIP
TODO test using as a function from a package
TODO test passing logger and setting up default loggers
"""

import time

from src.websnap.validators import get_config_parser, validate_log_config
from src.websnap.logger import get_custom_logger

__all__ = ["websnap"]

LOGGER_NAME = "websnap"


# TODO add validation for section config and add s3_config.ini config
# TODO add argument to CLI:  has_s3_writer: bool = False
# TODO test with different paths to config and s3_config
def websnap(
    config: str = "./config/config.ini",
    log_level: str = "INFO",
    has_file_logs: bool = False,
    has_s3_uploader: bool = False,
    s3_config: str = "./config/s3_config.ini",
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
        s3_config: Path to ini file used for S3 config.
        repeat_interval: Run websnap continuously every <repeat> minutes, if omitted
            then default value is None and websnap will not repeat.
    """
    # Validate log config and setup logging
    try:
        parser = get_config_parser(config)
        log_conf = validate_log_config(parser)
        log = get_custom_logger(
            name=LOGGER_NAME,
            level=log_level,
            has_file_logs=has_file_logs,
            config=log_conf,
        )
    except Exception as e:
        print(f"ERROR: {e}")
        return

    # Validate S3 config
    if has_s3_uploader:
        try:
            parser_s3 = get_config_parser(s3_config)
            # TODO WIP start dev here, add validator for parser_s3
        except Exception as e:
            log.error({e})
            return

    # Download and write URLs
    is_repeat = True
    while is_repeat:

        # Do not repeat iteration if repeat_interval is None
        is_repeat = repeat_interval is not None

        start_time = time.time()
        log.info("Started websnap iteration")

        # TODO remove
        time.sleep(1)

        # TODO URLs processing here, call logic.process_urls()

        log.info("Finished websnap iteration")
        exec_time = int(time.time() - start_time)

        if is_repeat:
            interval_seconds = int(repeat_interval) * 60
            if interval_seconds > exec_time:
                wait_time = interval_seconds - exec_time
                log.info(f"Sleeping {wait_time} seconds before next iteration...")
                time.sleep(wait_time)

    return
