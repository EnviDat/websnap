"""
Class and functions used to download and write files hosted at URLs to S3 bucket or
local machine.

TODO finish WIP
TODO test using as a function from a package
"""

from src.websnap.validators import get_config_parser, validate_log_config
from src.websnap.logger import get_logger

__all__ = ["websnap"]


# TODO implement repeat
# TODO refactor to use functional programming rather than class approach
def websnap(
    config: str = "./config/config.ini",
    loglevel: str = "INFO",
    repeat: int | None = None,
):
    """
    Download and write files hosted at URLs to S3 bucket or local machine.
    Optionally repeat websnap.

    Args:
        config (str): path to 'config.ini' file. Default value is './config/config.ini'
        loglevel (str): level to use for logging, default value is 'INFO'
        repeat (int | None): run websnap continuously every <repeat> minutes, if omitted
            then default value is None and websnap will not repeat
    """
    try:
        snapper = WebSnapper(config=config, loglevel=loglevel, repeat=repeat)

        # TODO remove
        # print(f"**TEST PROPERTY:  {snapper.log_config}")

        snapper.write_urls()

    except Exception as e:
        print(f"ERROR: {e}")


# TODO add boolean argument has_rotating_logs (also add to cli but call rotating_logs)
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

    @property
    def loglevel(self):
        return self._loglevel

    @loglevel.setter
    def loglevel(self, value):
        try:
            self._loglevel = value.upper()
        except AttributeError:
            raise Exception("Argument loglevel must be a string")

    # TODO add validation for section config and add secrets.ini config and
    #  validation for bucket values

    # TODO extract methods and property with external functions to another module

    @property
    def log_config(self):
        if not (config_parser := get_config_parser(self.config)):
            raise Exception("Could not parse config file, check console logs")
        return validate_log_config(config_parser)

    # def validate_config(self) -> LogConfigModel | Exception:
    #     """
    #     Return validated config objects.
    #     """
    #     if not (config_parser := get_config_parser(self.config)):
    #         raise Exception("Could not parse config file, check console logs")
    #
    #     log_config = get_log_config(config_parser)
    #     return log_config

    # TODO finish function
    def write_urls(self):
        """
        Download and write files hosted at URLs to S3 bucket or local machine.
        """
        log = get_logger("websnap", self.loglevel)
        log.info("*** Start transfer...")
