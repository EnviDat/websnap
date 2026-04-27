"""
CLI that supports copying files hosted at URLs in config and then uploading
them to S3 bucket or local machine.

Example pdm command without flags (uses default argument values):
    pdm run websnap-cli

Example pdm command, writes files locally:
pdm run websnap-cli --file-logs

Example pdm command, uploads files to a S3 bucket:
pdm run websnap-cli --file-logs --s3-uploader --backup-s3-count 3

Example command to run command directly with python
from project root directory without flags:
    python -m src.websnap.websnap_cli
"""

import argparse
import sys

import websnap
from websnap.constants import TIMEOUT


def parse_arguments() -> argparse.Namespace:
    """
    Parses command line arguments and return arguments as argparse.Namespace object.
    If parsing fails then return None.
    """

    parser = argparse.ArgumentParser(
        description="Supports copying files hosted at URLs in "
        "config and then uploading them to S3 bucket or local machine."
    )

    parser.add_argument(
        "--config",
        default="config.ini",
        help="Path to configuration file.Default value is 'config.ini'.",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Level to use for logging. Default value is 'INFO'.",
    )

    parser.add_argument(
        "--file-logs", action="store_true", help="Enable rotating file logs."
    )

    parser.add_argument(
        "--s3-uploader",
        action="store_true",
        help="Enable uploading of files to S3 bucket. ",
    )

    parser.add_argument(
        "--profile-name",
        help="Name of a profile to use for S3 shared credentials file. "
        "If omitted then the default profile is used.",
    )

    parser.add_argument(
        "--endpoint-url", help="Complete URL to use for the constructed S3 client."
    )

    parser.add_argument(
        "--backup-s3-count",
        type=int,
        help="Copy and backup S3 objects in each config section"
        "<backup-s3-count> times, "
        "remove object with the oldest last modified timestamp. "
        "If omitted then objects are not copied or removed.",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=TIMEOUT,
        help="Number of seconds to wait for response for each HTTP request.",
    )

    parser.add_argument(
        "--early-exit",
        action="store_true",
        help="Enable early program termination after error occurs. "
        "If omitted then logs URL processing errors "
        "but continues program execution.",
    )

    parser.add_argument(
        "--section-config",
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

    try:
        websnap.websnap(
            config=kwargs["config"],
            log_level=kwargs["log_level"],
            file_logs=kwargs["file_logs"],
            s3_uploader=kwargs["s3_uploader"],
            profile_name=kwargs["profile_name"],
            endpoint_url=kwargs["endpoint_url"],
            backup_s3_count=kwargs["backup_s3_count"],
            timeout=kwargs["timeout"],
            early_exit=kwargs["early_exit"],
            section_config=kwargs["section_config"],
        )

    except (
        ValueError,
        FileNotFoundError,
        TypeError,
        ConnectionError,
        RuntimeError,
        TimeoutError,
    ) as e:
        sys.exit(f"ERROR: {e}")
