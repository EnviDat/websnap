"""
Scripts that is used to download and write files hosted at URLs to S3 bucket or
local machine.

TODO finish WIP
TODO write comments including example commands
TODO test using as a function from a package

Example command from websnap/src/websnap:
    python websnap.py
"""

from src.websnap.config import read_config
from src.websnap.logger import get_logger

__all__ = ["websnap"]


# TODO review if function should be below WebSnapper class
def websnap(loglevel: str = "INFO", repeat: int | None = None):
    """
    Download and write files hosted at URLs to S3 bucket or local machine.
    :rtype: object
    """
    snapper = WebSnapper(loglevel=loglevel, repeat=repeat)
    snapper.validate_config()
    snapper.write_urls()


class WebSnapper:
    def __init__(
        self,
        config: str = "config.ini",
        loglevel: str = "INFO",
        repeat: int | None = None,
    ):
        self.config = config
        self.loglevel = loglevel
        self.repeat = repeat

    # TODO WIP debug config file path
    def validate_config(self):
        """
        Return validated config object.
        """
        read_config(self.config)

    def write_urls(self):
        """
        Download and write files hosted at URLs to S3 bucket or local machine.
        """

        # TODO remove print statements
        # print(f"loglevel:  {self.loglevel}")
        # print(f"repeat:   {self.repeat}")

        # TODO refactor logger to use config (with default) values
        log = get_logger("websnap", self.loglevel)
        log.info("*** Start transfer...")
