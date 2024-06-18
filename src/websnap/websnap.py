"""
Scripts that is used to download and write files hosted at URLs to S3 bucket or
local machine.

TODO finish WIP
TODO write comments including example commands
TODO test using as a function from a package

Example command from websnap/src/websnap:
    python websnap.py
"""

from src.websnap.logger import get_logger


def write_urls(loglevel: str = "INFO", repeat: int | None = None):
    """
    Download and write files hosted at URLs to S3 bucket or local machine.
    """

    # TODO remove print statements
    print(f"loglevel:  {loglevel}")
    print(f"repeat:   {repeat}")

    # TODO start dev here: read config file

    # TODO refactor logger to use config (with default) values
    log = get_logger("websnap", loglevel)
    log.info("*** Start transfer...")
