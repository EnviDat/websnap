"""
CLI that supports copying files hosted at URLs in config and then uploading
them to S3 bucket or local machine.

Example pdm command without flags (uses default argument values):
    pdm run websnap-cli

Example pdm command, writes files locally and repeats every 60 minutes (1 hour):
pdm run websnap-cli --file_logs --repeat_minutes 60

Example pdm command, uploads files to a S3 bucket and
repeats every 1440 minutes (24 hours):
pdm run websnap-cli --file_logs --s3_uploader --backup_s3_count 3 --repeat_minutes 1440

Example command to run command directly with python
from project root directory without flags:
    python -m src.websnap.websnap_cli
"""

import argparse
import websnap
from websnap.constants import TIMEOUT


def parse_arguments() -> argparse.Namespace | None:
    """
    Parses command line arguments and return arguments as argparse.Namespace object.
    If parsing fails then return None.
    """

    parser = argparse.ArgumentParser(
        description="Supports copying files hosted at URLs in "
        "config and then uploading them to S3 bucket or local machine."
    )

    parser.add_argument(
        "-c",
        "--config",
        default="config.ini",
        help="Path to configuration file." "Default value is 'config.ini'.",
    )

    parser.add_argument(
        "-l",
        "--log_level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Level to use for logging. Default value is 'INFO'.",
    )

    parser.add_argument(
        "-f", "--file_logs", action="store_true", help="Enable rotating file logs."
    )

    parser.add_argument(
        "-s",
        "--s3_uploader",
        action="store_true",
        help="Enable uploading of files to S3 bucket. ",
    )

    parser.add_argument(
        "-b",
        "--backup_s3_count",
        type=int,
        help="Copy and backup S3 objects in each config section"
        "<backup_s3_count> times, "
        "remove object with the oldest last modified timestamp. "
        "If omitted then objects are not copied or removed.",
    )

    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=TIMEOUT,
        help="Number of seconds to wait for response for each HTTP request.",
    )

    parser.add_argument(
        "-e",
        "--early_exit",
        action="store_true",
        help="Enable early program termination after error occurs. "
        "If omitted then logs URL processing errors "
        "but continues program execution.",
    )

    parser.add_argument(
        "-r",
        "--repeat_minutes",
        type=int,
        help="Run websnap continuously every <repeat_minutes>. "
        "If omitted then websnap does not repeat.",
    )

    parser.add_argument(
        "-n",
        "--section_config",
        help="File or URL to obtain additional configuration sections. "
        "Cannot be used to assign DEFAULT section in config. "
        "Only currently supports JSON config.",
    )

    return parser.parse_args()


def main():
    """
    Main entry point for websnap-cli.
    """
    kwargs = vars(parse_arguments())

    websnap.websnap(
        config=kwargs["config"],
        log_level=kwargs["log_level"],
        file_logs=kwargs["file_logs"],
        s3_uploader=kwargs["s3_uploader"],
        backup_s3_count=kwargs["backup_s3_count"],
        timeout=kwargs["timeout"],
        early_exit=kwargs["early_exit"],
        repeat_minutes=kwargs["repeat_minutes"],
        section_config=kwargs["section_config"],
    )
