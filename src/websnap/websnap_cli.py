"""
Script that is used to download and write files hosted at URLs to S3 bucket or
local machine.

TODO write comments including example commands
TODO investigate running as single-line script with dependencies or building an
    exectuable script

Example pdm command without flags (uses default argument values):
    pdm run websnap-cli

TODO add flags
Example pdm command with flags:
    pdm run websnap-cli

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

    parser = argparse.ArgumentParser(description="Websnap CLI")

    parser.add_argument(
        "-c",
        "--config",
        default="./src/websnap/config/config.ini",
        help="Path to 'config.ini' file."
        "Default value is './src/websnap/config/config.ini'.",
    )

    parser.add_argument(
        "-l",
        "--loglevel",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Level to use for logging. Default value is'INFO'.",
    )

    parser.add_argument(
        "-f", "--file_logs", action="store_true", help="Enable rotating file logs."
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
    Download and write files hosted at URLs to S3 bucket or local machine.
    """
    kwargs = vars(parse_arguments())

    r_interval = kwargs["repeat"] if kwargs["repeat"] else None

    websnap.websnap(
        config=kwargs["config"],
        log_level=kwargs["loglevel"],
        has_file_logs=kwargs["file_logs"],
        repeat_interval=r_interval,
    )


if __name__ == "__main__":
    main()
