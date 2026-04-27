"""
Functions used to copy and write files retrieved from an API to a local machine.
"""

import configparser
import logging
import os

import requests
import sys

from websnap.session import make_session
from websnap.validators import validate_config_section


def terminate_program(early_exit: bool):
    """Terminates program execution if argument early_exit is True."""
    if early_exit:
        sys.exit("Error occurred: check logs for details")
    return


def get_url_content(
    url: str,
    section: str,
    log: logging.Logger,
    timeout: int = 32,
    early_exit: bool = False,
) -> bytes | None:
    """
    Return content of response from HTTP GET request.
    If response times out or response status code is >= 400 then terminate program if
    argument early_exit is True, else return None.

    Args:
        url: URL to download.
        section: Name of config section being processed.
        log: Logger object created with customized configuration file.
        timeout: Number of seconds to wait for response.
        early_exit: If True then terminates program immediately after error occurs.
            Default value is False.
            If False then only logs error and continues execution.
    """
    try:
        response = make_session().get(url, timeout=timeout)

        if not response.ok:
            log.error(
                f"Config section '{section}': "
                f"URL returned unsuccessful HTTP response "
                f"status code {response.status_code}"
            )
            terminate_program(early_exit)
            return None

        return response.content

    except requests.exceptions.Timeout:
        log.error(
            f"Config section '{section}': "
            f"URL timed out while waiting {timeout} seconds for response"
        )

    except requests.exceptions.SSLError:
        log.error(f"Config section '{section}': SSL certificate error for URL '{url}'")

    except requests.exceptions.ConnectionError:
        log.error(
            f"Config section '{section}': "
            f"Connection failed for URL '{url}': "
            f"check DNS, network, or if the server is running"
        )

    except requests.exceptions.RequestException as err:
        log.error(
            f"Config section '{section}': "
            f"Unexpected request error for URL '{url}': {err}"
        )

    terminate_program(early_exit)
    return None


def is_min_size_kb(
    url_content: bytes,
    min_size_kb: int,
    section: str,
    log: logging.Logger,
    early_exit: bool = False,
) -> bool:
    """
    Return True if url_content is greater than min_size_kb.
    Else return False or terminate program (if argument early_exit is True).

    Args:
        url_content: Content of response from HTTP request.
        min_size_kb: Minimum threshold in kilobytes that URL response content must be to
            write or upload file.
        section: Name of config section being processed.
        log: Logger object created with customized configuration file.
        early_exit: If True then terminates program immediately after error occurs.
            Default value is False.
            If False then only logs error and continues execution.
    """
    data_kb = len(url_content) / 1024

    if data_kb < min_size_kb:
        log.error(
            f"Config section '{section}': "
            f"URL response content in config section {section} is less than "
            f"config value 'min_size_kb' {min_size_kb}"
        )
        terminate_program(early_exit)
        return False

    return True


def write_urls_locally(
    conf_parser: configparser.ConfigParser,
    log: logging.Logger,
    min_size_kb: int,
    timeout: int = 32,
    early_exit: bool = False,
) -> None:
    """
    Download files hosted at URLS in config and then write them to local machine.

    Args:
        conf_parser: ConfigParser object created from parsing configuration file.
        log: Logger object created with customized configuration file.
        min_size_kb: Minimum threshold in kilobytes that URL response content must be to
            write file.
        timeout: Number of seconds to wait for response.
        early_exit: If True then terminates program immediately after error occurs.
            Default value is False.
            If False then only logs error and continues execution.
    """
    for section in conf_parser.sections():
        try:
            conf = validate_config_section(conf_parser, section)
        except ValueError as e:
            log.error(e)
            terminate_program(early_exit)
            continue

        if conf.directory and not os.path.isdir(conf.directory):
            log.error(
                f"Config section '{section}': directory '{conf.directory}' "
                f"does not exist"
            )
            terminate_program(early_exit)
            continue

        url_content = get_url_content(str(conf.url), section, log, timeout, early_exit)
        if url_content is None:
            continue

        is_min_size = is_min_size_kb(url_content, min_size_kb, section, log, early_exit)
        if not is_min_size:
            continue

        if conf.directory:
            file_path = f"{conf.directory}/{conf.file_name}"
        else:
            file_path = f"{conf.file_name}"

        with open(file_path, "wb") as f:
            f.write(url_content)
            log.info(
                f"Successfully downloaded URL content and wrote file locally in "
                f"config section: {section}"
            )

    return
