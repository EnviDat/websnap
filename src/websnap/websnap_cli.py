"""
CLI that supports downloading files hosted at URLs in config and then uploading
them to S3 bucket or local machine.

Example pdm command without flags (uses default argument values):
    pdm run websnap-cli

Example pdm command, writes files locally and repeats every 60 minutes (1 hour):
pdm run websnap-cli --file_logs --repeat 60

Example pdm command, uploads files to a S3 bucket and
repeats every 1440 minutes (24 hours):
    pdm run websnap-cli --file_logs --s3_uploader --backup_s3_count 3 --repeat 1440

Example command to run command directly with python
from project root directory without flags:
    python -m src.websnap.websnap_cli
"""

import argparse
from src.websnap import websnap


def parse_arguments() -> argparse.Namespace | None:
    """
    Parses command line arguments and return arguments as argparse.Namespace object.
    If parsing fails then return None.
    """

    parser = argparse.ArgumentParser(
        description="Websnap CLI: Supports downloading files hosted at URLs in config "
        "and then uploading them to S3 bucket or local machine."
    )

    parser.add_argument(
        "-c",
        "--config",
        default="./src/websnap/config/config.ini",
        help="Path to configuration file."
        "Default value is './src/websnap/config/config.ini'.",
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
        "-s", "--s3_uploader", action="store_true", help="Enable S3 uploader."
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
        "-e",
        "--early_exit",
        action="store_true",
        help="Enable early program termination after error occurs. "
        "If ommitted then logs URL processing errors "
        "but continues program execution.",
    )

    parser.add_argument(
        "-r",
        "--repeat",
        type=int,
        help="Run websnap continuously every <repeat> minutes. "
        "If omitted then websnap does not repeat.",
    )

    try:
        return parser.parse_args()
    except (argparse.ArgumentTypeError, Exception) as e:
        print(f"Exception: {e} ")
        return None


def main():
    """
    Main entry point for websnap-cli.
    """
    kwargs = vars(parse_arguments())

    websnap.websnap(
        config=kwargs["config"],
        log_level=kwargs["log_level"],
        has_file_logs=kwargs["file_logs"],
        is_s3_uploader=kwargs["s3_uploader"],
        backup_s3_count=kwargs["backup_s3_count"],
        has_early_exit=kwargs["early_exit"],
        repeat_interval=kwargs["repeat"],
    )


if __name__ == "__main__":
    main()
