"""
Scripts that is used to download and write files hosted at URLs to S3 bucket or
local machine.

TODO finish WIP
TODO write comments including example commands

Example command from websnap/src/websnap:
    python websnap.py
"""

import argparse

from logger import get_logger


def parse_arguments() -> argparse.Namespace | None:
    """
    Parses command line arguments and return arguments as argparse.Namespace object.
    If parsing fails then return None.
    """

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-l",
        "--loglevel",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Level to use for logging. Default value is'INFO'.",
    )

    parser.add_argument(
        "-r",
        "--repeat",
        type=int,
        help="Run websnap continuously every <repeat> minutes.",
    )

    try:
        return parser.parse_args()
    except (argparse.ArgumentTypeError, Exception) as e:
        print(f"Exception: {e} ")
        return None


def websnap():
    """
    Download and write files hosted at URLs to S3 bucket or local machine.
    """
    args = parse_arguments()

    log = get_logger(websnap.__name__, args.loglevel)
    log.info("*** Start transfer...")

    # TODO start dev here: read config file


if __name__ == "__main__":
    websnap()
