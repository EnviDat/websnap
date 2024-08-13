"""Config utilities, parses and validates config .ini files."""

import configparser
from pathlib import Path
from pydantic import (
    BaseModel,
    ValidationError,
    PositiveInt,
    AnyHttpUrl,
    AnyUrl,
    field_validator,
    NonNegativeInt,
)
from typing import Optional

from websnap.constants import LogRotation, MIN_SIZE_KB


def get_config_parser(config_path: str) -> configparser.ConfigParser | Exception:
    """
    Return ConfigParser object.
    Returns Exception if fails.

    Args:
        config_path (str): Path to config.ini file.
    """
    try:
        config_file = Path(config_path)
        config = configparser.ConfigParser()
        conf = config.read(config_file)

        if not conf:
            return Exception(f"File {config_path} not found")

        if len(config.sections()) < 1:
            return Exception(
                f"File '{config_path}' not valid config, " f"does not have any sections"
            )

        return config

    except Exception as e:
        return Exception(f"{e}")


class LogConfigModel(BaseModel):
    """
    Class with required log config values and their types.
    """

    log_when: str
    log_interval: PositiveInt
    log_backup_count: NonNegativeInt


def validate_log_config(
    config_parser: configparser.ConfigParser,
) -> LogConfigModel | Exception:
    """
    Return LogConfigModel object.
    Returns Exception if parsing fails.

    Args:
        config_parser (configparser.ConfigParser): ConfigParser object
    """
    try:
        log = {
            "log_when": config_parser.get(
                "DEFAULT", "log_when", fallback=LogRotation.WHEN.value
            ),
            "log_interval": config_parser.get(
                "DEFAULT", "log_interval", fallback=LogRotation.INTERVAL.value
            ),
            "log_backup_count": config_parser.getint(
                "DEFAULT", "log_backup_count", fallback=LogRotation.BACKUP_COUNT.value
            ),
        }
        return LogConfigModel(**log)
    except ValidationError as e:
        return Exception(f"Failed to validate config, error(s): {e}")
    except ValueError as e:
        return Exception(f"Incorrect log related value in config, error(s): {e}")
    except Exception as e:
        return Exception(f"{e}")


def validate_min_size_kb(config_parser: configparser.ConfigParser) -> int | Exception:
    """
    Return min_size_kb from config as integer.
    Returns Exception if validation fails.

    Args:
        config_parser: ConfigParser object
    """
    try:
        min_size_kb = config_parser.getint(
            "DEFAULT", "min_size_kb", fallback=MIN_SIZE_KB
        )
        if min_size_kb >= 0:
            return min_size_kb
        else:
            raise ValueError(
                "Value for config value 'min_size_kb' must be greater than 0"
            )
    except ValidationError as e:
        return Exception(f"Failed to validate config value 'min_size_kb, error(s): {e}")
    except ValueError as e:
        return Exception(
            f"Incorrect value for config value 'min_size_kb', error(s): {e}"
        )
    except Exception as e:
        return Exception(f"{e}")


class ConfigSectionModel(BaseModel):
    """
    Class with required config section values (for writing to local machine).
    """

    url: AnyHttpUrl
    file_name: str
    directory: Optional[str] = None


def validate_config_section(
    config_parser: configparser.ConfigParser, section: str
) -> ConfigSectionModel | Exception:
    """
    Return ConfigSectionModel object.
    Returns Exception if parsing fails.

    Args:
        config_parser: ConfigParser object
        section: Name of section being validated
    """
    try:
        conf_section = {
            "url": config_parser.get(section, "url"),
            "file_name": config_parser.get(section, "file_name"),
        }
        if directory := config_parser.get(section, "directory", fallback=None):
            conf_section["directory"] = directory
        return ConfigSectionModel(**conf_section)
    except ValidationError as e:
        return Exception(
            f"Failed to validate config section '{section}', error(s): {e}"
        )
    except ValueError as e:
        return Exception(
            f"Incorrect value in config section '{section}', error(s): {e}"
        )
    except Exception as e:
        return Exception(f"{e}")


class S3ConfigModel(BaseModel):
    """
    Class with required S3 config values and their types.
    """

    endpoint_url: AnyUrl
    aws_access_key_id: str
    aws_secret_access_key: str


def validate_s3_config(
    config_parser: configparser.ConfigParser,
) -> S3ConfigModel | Exception:
    """
    Return S3ConfigModel object.
    Returns Exception if parsing fails.

    Args:
        config_parser (configparser.ConfigParser): ConfigParser object
    """
    try:
        s3_conf = {
            "endpoint_url": config_parser.get("DEFAULT", "endpoint_url"),
            "aws_access_key_id": config_parser.get("DEFAULT", "aws_access_key_id"),
            "aws_secret_access_key": config_parser.get(
                "DEFAULT", "aws_secret_access_key"
            ),
        }
        return S3ConfigModel(**s3_conf)
    except ValidationError as e:
        return Exception(f"Failed to validate S3 config, error(s): {e}")
    except ValueError as e:
        return Exception(f"Incorrect value in S3 config, error(s): {e}")
    except Exception as e:
        return Exception(e)


class S3ConfigSectionModel(BaseModel):
    """
    Class with required config section values (for writing to S3 bucket).
    """

    url: AnyUrl
    bucket: str
    key: str

    @field_validator("key")
    @classmethod
    def key_must_contain_period(cls, v: str) -> str:
        key_split = v.rpartition(".")
        if not key_split[1]:
            raise ValueError("Config section key requires a file extension")
        return v

    @field_validator("key")
    @classmethod
    def key_must_not_start_with_slash(cls, v: str) -> str:
        if v.startswith("/"):
            raise ValueError("Config section key cannot start with a '/'")
        return v


def validate_s3_config_section(
    config_parser: configparser.ConfigParser, section: str
) -> S3ConfigSectionModel | Exception:
    """
    Return S3ConfigSectionModel object.
    Returns Exception if parsing fails.

    Args:
        config_parser: ConfigParser object
        section: Name of section being validated
    """
    try:
        conf_section = {
            "url": config_parser.get(section, "url"),
            "bucket": config_parser.get(section, "bucket"),
            "key": config_parser.get(section, "key"),
        }
        return S3ConfigSectionModel(**conf_section)
    except ValidationError as e:
        return Exception(
            f"Failed to validate config section '{section}', error(s): {e}"
        )
    except ValueError as e:
        return Exception(
            f"Incorrect value in config section '{section}', error(s): {e}"
        )
    except Exception as e:
        return Exception(f"{e}")
