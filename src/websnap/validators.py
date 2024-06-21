"""Config utilities, parses and validates config .ini files."""

import configparser
from pathlib import Path
from pydantic import BaseModel, ValidationError, field_validator

from src.websnap.constants import LogRotation


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
            raise Exception(f"File {config_path} not found")

        if len(config.sections()) < 1:
            raise Exception(
                f"File '{config_path}' not valid config, does not have any sections"
            )

        return config

    except Exception as e:
        raise Exception(f"{e}")


class LogConfigModel(BaseModel):
    """
    Class with required log config values and their types.
    """

    log_when: str
    log_interval: int
    log_backup_count: int

    @field_validator("log_interval", "log_backup_count")
    def backup_count_is_non_negative(cls, value: int):
        if value < 0:
            raise ValueError("Config value must be greater than 0.")
        return value


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
        raise Exception(f"Failed to validate config, error(s): {e}")
    except ValueError as e:
        raise Exception(f"Incorrect log related value in config, error(s): {e}")
    except Exception as e:
        raise Exception(f"{e}")
