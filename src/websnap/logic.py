"""
Supporting functions used to download and write files hosted
at URLs to S3 bucket or local machine.
"""

import configparser
import logging
import os
import requests
import boto3

from src.websnap.validators import validate_config_section, S3ConfigModel


# TODO test with CLI
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
                    f"Config section '{section}': directory '{conf.directory}' "
                    f"does not exist"
                )
                continue

            url = str(conf.url)
            response = requests.get(url)

            if not response.ok:
                log.error(
                    f"Config section '{section}': "
                    f"URL returned unsuccessful HTTP response "
                    f"status code {response.status_code}"
                )
                continue

            data = response.content

            # TODO test
            data_kb = data.__sizeof__() / 1024
            if data_kb < min_size_kb:
                log.error(
                    f"Config section '{section}': "
                    f"URL response content in config section {section} is less than "
                    f"config value 'min_size_kb' {min_size_kb}"
                )
                continue

            file_path = f"{conf.directory}/{conf.file_name}"
            with open(file_path, "wb") as f:
                f.write(data)
                log.info(
                    f"Successfully downloaded URL content and wrote file in "
                    f"config section: {section}"
                )

        except Exception as e:
            log.error(f"Config section '{section}', error(s): {e}")

    return


# TODO finish WIP, start dev here
# TODO test with CLI
# TODO review function
def write_urls_to_s3(
    conf_parser: configparser.ConfigParser,
    conf_s3: S3ConfigModel,
    log: logging.getLogger,
    min_size_kb: int,
) -> None | Exception:
    """
    Download files hosted at URLS in config and then upload them to S3 bucket.

    Args:
        conf_parser: ConfigParser object created from parsing configuration file.
        conf_s3: S3ConfigModel object created from validated configuration file.
        log: Logger object created with customized configuration file.
        min_size_kb: Minimum threshold in kilobytes that URL response content must be to
            upload file to S3 bucket.
    """
    session = boto3.Session(
        aws_access_key_id=conf_s3.aws_access_key_id,
        aws_secret_access_key=conf_s3.aws_secret_access_key,
    )

    session.client(service_name="s3", endpoint_url=str(conf_s3.endpoint_url))

    for section in conf_parser.sections():

        pass

    return
