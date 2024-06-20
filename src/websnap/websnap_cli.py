"""
Scripts that is used to download and write files hosted at URLs to S3 bucket or
local machine.

TODO write comments including example commands
TODO investigate running as sing-glie script with dependencies or bulding an exectuable
    script

Example command:
    pdm run websnap-cli
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
        help="Path to 'config.ini' file. "
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


def main():
    """
    Main entry point for websnap-cli.
    Download and write files hosted at URLs to S3 bucket or local machine.
    """
    kwargs = parse_arguments()
    websnap.websnap(**(vars(kwargs)))


if __name__ == "__main__":
    main()
