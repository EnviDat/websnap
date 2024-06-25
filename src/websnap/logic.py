"""
Supporting functions used to download and write files hosted
at URLs to S3 bucket or local machine.
"""

import configparser
import logging
import os

import requests

from src.websnap.validators import validate_config_section


# TODO test with CLI
# TODO review function
def write_urls_locally(
    conf_parser: configparser.ConfigParser, log: logging.getLogger, min_size_kb: int
) -> None | Exception:
    """
    Download files hosted at URLS in config and then upload them to local machine.

    Args:
        conf_parser: ConfigParser object created from parsing configuration file.
        log: Logger object created with customized configuration file.
        min_size_kb: Minimum threshold in kilobytes that URL response content must be to
            write file.
    """
    for section in conf_parser.sections():

        try:
            conf = validate_config_section(conf_parser, section)

            if not os.path.isdir(conf.directory):
                log.error(
                    f"Failed to write file in section '{section}': "
                    f"Config section '{section}' directory '{conf.directory}' "
                    f"does not exist"
                )
                continue

            url = str(conf.url)
            response = requests.get(url)

            if not response.ok:
                log.error(
                    f"Failed to write file in section '{section}': "
                    f"URL returned unsuccessful HTTP response "
                    f"status code {response.status_code}"
                )
                continue

            data = response.content
            data_kb = data.__sizeof__() / 1024

            if data_kb >= min_size_kb:
                # TODO test with extra slashes in directory and file_name
                # TODO test with absolute path
                file_path = f"{conf.directory}/{conf.file_name}"
                with open(file_path, "wb") as f:
                    f.write(data)
                    log.info(
                        f"Successfully downloaded URL content and wrote file in "
                        f"config section: {section}"
                    )
            else:
                # TODO test
                log.error(
                    f"Failed to write file in section '{section}': "
                    f"URL content in config section {section} is less than "
                    f"config value 'min_size_kb' {min_size_kb}"
                )

        except Exception as e:
            log.error(f"Failed to write file in section '{section}', error(s): {e}")

    return
