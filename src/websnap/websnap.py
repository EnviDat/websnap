"""
Function websnap is used to download and write files hosted at URLs to
S3 bucket or local machine.
Supports customized file rotational logging.
Optionally repeats.

TODO finish WIP
TODO test using as a function from a package
TODO test passing logger and setting up default loggers
"""

import time

from src.websnap.validators import get_config_parser, validate_log_config
from src.websnap.logger import get_custom_logger

__all__ = ["websnap"]

LOGGER_NAME = "websnap"


# TODO add validation for section config and add secrets.ini config and
#  validation for bucket values
def websnap(
    config: str = "./config/config.ini",
    log_level: str = "INFO",
    has_file_logs: bool = False,
    repeat_interval: int | None = None,
):
    """
    Download and write files hosted at URLs to S3 bucket or local machine.
    Optionally customize rotating logs.
    Optionally repeat websnap file processing iteration.

    Args:
        config: Path to 'config.ini' file.
        log_level: Level to use for logging.
        has_file_logs: If True then implements rotating file logs.
        repeat_interval: run websnap continuously every <repeat> minutes, if omitted
            then default value is None and websnap will not repeat.
    """

    # Parse config and setup log
    try:
        conf = get_config_parser(config)
        log_conf = validate_log_config(conf)
        log = get_custom_logger(
            name=LOGGER_NAME,
            level=log_level,
            has_file_logs=has_file_logs,
            config=log_conf,
        )
    except Exception as e:
        print(f"ERROR: {e}")
        return

    # File processing repeat loop
    is_repeat = True
    while is_repeat:

        # Do not repeat iteration if repeat_interval is None
        is_repeat = repeat_interval is not None

        start_time = time.time()
        log.info("Start websnap iteration")

        # TODO remove
        time.sleep(2)

        # TODO add log validation and file processing here

        log.info("Finished websnap iteration")
        exec_time = int(time.time() - start_time)

        # If is_repeat is True wait during time left in repeat_interval
        # before next iteration
        if is_repeat:
            interval_seconds = int(repeat_interval) * 60
            if interval_seconds > exec_time:
                wait_time = interval_seconds - exec_time
                log.info(f"Sleeping {wait_time} seconds before next iteration...")
                time.sleep(wait_time)

    return


# # TODO finish function in another module
# def write_urls(self):
#     """
#     Download and write files hosted at URLs to S3 bucket or local machine.
#     """
#     log.info("*** Start transfer...")
