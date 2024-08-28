"""Config utilities, parses and validates config .ini files."""

import argparse
import configparser
import json
from pathlib import Path
from pydantic import (
    BaseModel,
    ValidationError,
    PositiveInt,
    AnyHttpUrl,
    AnyUrl,
    field_validator,
    NonNegativeInt,
    TypeAdapter,
)
from typing import Optional, Any

from websnap.constants import LogRotation, MIN_SIZE_KB


def validate_positive_integer(x: Any) -> int | Exception:
    """
    Return x if it is a positive integer.
    Return Exception if x is not a positive integer.

    Args:
        x: The input value.
    """
    ta = TypeAdapter(PositiveInt)

    try:
        ta.validate_python(x)
        return x
    except ValidationError as e:
        return Exception(
            f"Invalid value {x} (it must be a positive integer), error: {e}"
        )


# TODO test function
def is_url(x: Any) -> bool:
    """
    Return True if x is a URL. Else return False.

     Args:
        x: The input value.
    """
    ta = TypeAdapter(AnyUrl)
    try:
        ta.validate_python(x)
        return True
    except ValidationError:
        return False


def get_json_config_parser(config_path: Path) -> configparser.ConfigParser | Exception:
    """
    Returns ConfigParser instance with items read from JSON config file.
    Returns Exception if fails.

    Args:
        config_path: Path object to the .json config file.
    """
    try:
        with open(config_path, "r") as config_file:
            data = json.load(config_file)

        config_parser = configparser.ConfigParser()

        for key, value in data.items():
            config_parser[key] = value

        return config_parser

    except FileNotFoundError:
        return Exception(f"File '{config_path}' not found")
    except Exception as e:
        return Exception(e)


# TODO WIP start dev here
# TODO handle URL to JSON config
# TODO test, including with intentional errors (wrong file path)
def get_json_section_config_parser(
    section_config: str,
) -> configparser.ConfigParser | Exception:
    """
    Returns ConfigParser instance with items read from JSON section config file.
    Cannot be used to assign DEFAULT section in returned ConfigParser instance.
    Returns Exception if fails.

    Args:
        section_config: File or URL to obtain additional configuration sections.
    """
    try:
        # TODO call is_url() to see if section_config is URL
        # TODO create section_parser from URL content

        # TODO move this to an else block after handling URL
        if (section_path := Path(section_config)).suffix == ".json":
            section_parser = get_json_config_parser(section_path)
            # TODO extract error handling to block below to handle URL errors as well
            if not isinstance(section_parser, configparser.ConfigParser):
                return Exception(section_parser)
        else:
            return Exception("Section config extension must be '.json'")

        # TODO implement isinstance() error handling here

        if section_parser.defaults():
            return Exception(f"Section config cannot have a 'DEFAULT' section")

        return section_parser

    except FileNotFoundError:
        return Exception(f"File '{section_config}' not found")
    except Exception as e:
        return Exception(e)


def get_config_parser(
    config: str, section_config: str | None
) -> configparser.ConfigParser | Exception:
    """
    Return ConfigParser object.
    Returns Exception if fails.
    If section_config passed then merges config and section_config
    into one ConfigParser instance.

    Args:
        config: Path to .ini or .json configuration file.
        section_config (str): File or URL to obtain additional configuration sections.
                              Default value is None.
    """
    try:
        conf_path = Path(config)

        if section_config and conf_path.suffix != ".json":
            return Exception(
                f"Config '{config}' extension must be '.json' to also use "
                f"optional section config '{section_config}'"
            )
        elif conf_path.suffix == ".json":
            config_parser = get_json_config_parser(conf_path)
            if not isinstance(config_parser, configparser.ConfigParser):
                return Exception(config_parser)
            if section_config:
                section_parser = get_json_section_config_parser(section_config)
                if not isinstance(section_parser, configparser.ConfigParser):
                    return Exception(section_parser)
                # TODO merge config_parser and section_parser into assigned
                #  combined_parser and then return combined_parser
                pass
        else:
            config_parser = configparser.ConfigParser()
            conf = config_parser.read(conf_path)
            if not conf:
                return Exception(f"File '{config}' not found")

        if len(config_parser.sections()) < 1:
            return Exception(f"File '{config}' does not have any sections")

        return config_parser

    except FileNotFoundError:
        return Exception(f"File '{config}' not found")
    except Exception as e:
        return Exception(e)


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
