"""
Class and functions used to download and write files hosted at URLs to S3 bucket or
local machine.

TODO finish WIP
TODO test using as a function from a package
"""

from src.websnap.validators import get_config_parser, validate_log_config
from src.websnap.logger import get_logger


__all__ = ["websnap"]


# TODO implement repeat (and in cli)
# TODO add validation for section config and add secrets.ini config and
#  validation for bucket values
def websnap(
    config: str = "./config/config.ini",
    log_level: str = "INFO",
    has_file_logs: bool = False,
    repeat: int | None = None,
):
    """
    Download and write files hosted at URLs to S3 bucket or local machine.
    Customize log output with optional rotating logs.
    Optionally repeat websnap.

    Args:
        config: Path to 'config.ini' file.
        log_level: Level to use for logging.
        has_file_logs: If True then implements rotating file logs.
        repeat: run websnap continuously every <repeat> minutes, if omitted
            then default value is None and websnap will not repeat.
    """
    try:
        conf = get_config_parser(config)
        log_config = validate_log_config(conf)

        log = get_logger(
            name="websnap",
            level=log_level,
            has_file_logs=has_file_logs,
            config=log_config,
        )

        # TODO remove or refactor
        log.info("*** Start me ...")

        pass

    except Exception as e:
        print(f"ERROR: {e}")


# # TODO finish function in another module
# def write_urls(self):
#     """
#     Download and write files hosted at URLs to S3 bucket or local machine.
#     """
#     log.info("*** Start transfer...")
