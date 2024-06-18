"""
Class and functions used to download and write files hosted at URLs to S3 bucket or
local machine.

TODO finish WIP
TODO test using as a function from a package
"""

from src.websnap.validators import get_config_parser, LogConfigModel, get_log_config
from src.websnap.logger import get_logger

__all__ = ["websnap"]


# TODO review if function should be below WebSnapper class
def websnap(**kwargs):
    """
    Download and write files hosted at URLs to S3 bucket or local machine.
    :rtype: object
    """
    try:
        snapper = WebSnapper(**kwargs)

        snapper.validate_config()
        # snapper.write_urls()

    except Exception as e:
        print(f"ERROR: {e}")


class WebSnapper:
    def __init__(
        self,
        config: str = "./config/config.ini",
        loglevel: str = "INFO",
        repeat: int | None = None,
    ):
        self.config = config
        self.loglevel = loglevel
        self.repeat = repeat

    # TODO add validation for section config and add secrets.ini config and
    #  validation for bucket values
    def validate_config(self) -> LogConfigModel | Exception:
        """
        Return validated config objects.
        """
        if not (config_parser := get_config_parser(self.config)):
            raise Exception("Could not parse config file, check console logs")

        log_config = get_log_config(config_parser)
        return log_config

    # TODO finish function
    def write_urls(self):
        """
        Download and write files hosted at URLs to S3 bucket or local machine.
        """
        log = get_logger("websnap", self.loglevel)
        log.info("*** Start transfer...")
