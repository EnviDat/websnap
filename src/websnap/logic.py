"""
Supporting functions used to download and write files hosted
at URLs to S3 bucket or local machine.
"""

import configparser


# TODO WIP finish function
# TODO condition if writing locally or to s3
# TODO validate conf for each section
def process_urls(
    conf: configparser.ConfigParser,
    has_s3_uploader: bool = False,
    s3_conf: configparser.ConfigParser | None = None,
):
    """
    Download files hosted at URLs in config and then uploads them
    to S3 bucket or local machine.

    Args:
        conf: ConfigParser object created from parsing configuration file.
        has_s3_uploader: If True then writes URLs to S3 bucket specified in s3_conf.
        s3_conf: ConfigParser objected created from parsing S3 configuration file.
    """
    pass
