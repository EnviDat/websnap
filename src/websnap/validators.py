"""Config utilities, parses and validates config .ini files."""

import configparser
import json
import os
from pathlib import Path

import requests
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
from dotenv import load_dotenv

from websnap.constants import LogRotation, MIN_SIZE_KB, TIMEOUT


def validate_positive_integer(x: Any) -> int:
    """
    Return x if it is a positive integer.

    Args:
        x: The input value.
    """
    ta = TypeAdapter(PositiveInt)

    try:
        ta.validate_python(x)
        return x
    except ValidationError:
        raise Exception(f"{x} is not a a positive integer")


def validate_positive_int_args(
    timeout: int, backup_s3_count: int | None = None, repeat_minutes: int | None = None
) -> None:
    """
    Return None if validation passes (arguments are positive integers).
    If validation fails then raises Exception.
    None values are allowed for arguments backup_s3_count and repeat_minutes
    (validation still passes).

    Args:
        timeout: Number of seconds to wait for response for each HTTP request.
            If integer passed then it must be a positive integer.
        backup_s3_count: Copy and backup S3 objects in each config section
            <backup_s3_count> times,
            remove object with the oldest last modified timestamp.
            If integer passed then it must be a positive integer.
        repeat_minutes: Run websnap continuously every <repeat> minutes
               If integer passed then it must be a positive integer.
    """
    param_arg_dict = {
        "timeout": timeout,
        "backup_s3_count": backup_s3_count,
        "repeat_minutes": repeat_minutes,
    }

    param = None
    try:
        for param, arg in param_arg_dict.items():
            if param == "timeout":
                validate_positive_integer(arg)
            elif arg is not None:
                validate_positive_integer(arg)
    except Exception as e:
        raise Exception(f"Invalid argument passed for parameter {param}: {e}")

    return


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


def merge_config_parsers(
    config_1: configparser.ConfigParser, config_2: configparser.ConfigParser
) -> configparser.ConfigParser:
    """
    Merges config_2 into config_1 and then return config_1.
    If sections or keys in config_2 exist in config_1,
    the values from config_2 will overwrite those in config_1.
    """
    for section in config_2.sections():

        if not config_1.has_section(section):
            config_1.add_section(section)

        for option, value in config_2.items(section):
            config_1.set(section, option, value)

    return config_1


def get_json_config_parser(config_path: Path) -> configparser.ConfigParser:
    """
    Returns ConfigParser instance with items read from JSON config file.

    Args:
        config_path: Path object to the .json config file.
    """
    try:
        with open(config_path, "r") as config_file:
            data = json.load(config_file)

        config_parser = configparser.ConfigParser()
        config_parser.read_dict(data)

        return config_parser

    except FileNotFoundError:
        raise Exception(f"File '{config_path}' not found")
    except Exception as e:  # pragma: no cover
        raise Exception(e)


def get_url_json_config_parser(
    config_url: str, timeout: int = TIMEOUT
) -> configparser.ConfigParser:
    """
    Returns ConfigParser instance with items read from JSON config URL.

    Args:
        config_url: URL with additional configuration sections.
        timeout: Number of seconds to wait for response for each HTTP request.
    """
    try:
        response = requests.get(config_url, timeout=timeout)

        if not response.ok:
            raise Exception(
                f"URL {config_url} returned unsuccessful "
                f"status code {response.status_code}"
            )

        data = response.json()

        config_parser = configparser.ConfigParser()
        config_parser.read_dict(data)

        return config_parser

    except requests.exceptions.Timeout:  # pragma: no cover
        raise Exception(
            f"URL {config_url} timed out while waiting {timeout} seconds for response"
        )
    except Exception as e:  # pragma: no cover
        raise Exception(e)


def get_json_section_config_parser(
    section_config: str, timeout: int = TIMEOUT
) -> configparser.ConfigParser:
    """
    Returns ConfigParser instance with items read from JSON section config file.
    Cannot be used to assign DEFAULT section in returned ConfigParser instance.

    Args:
        section_config: File or URL with additional configuration sections.
        timeout: Number of seconds to wait for response for each HTTP request.
    """
    try:

        if is_url(section_config):
            section_parser = get_url_json_config_parser(section_config, timeout)
        else:
            if (section_path := Path(section_config)).suffix == ".json":
                section_parser = get_json_config_parser(section_path)
            else:
                raise Exception("Section config extension must be '.json'")

        if not isinstance(section_parser, configparser.ConfigParser):
            raise Exception(section_parser)

        if section_parser.defaults():
            raise Exception(f"Section config cannot have a 'DEFAULT' section")

        return section_parser

    except Exception as e:  # pragma: no cover
        raise Exception(e)


def get_config_parser(
    config: str, section_config: str | None = None, timeout: int = TIMEOUT
) -> configparser.ConfigParser:
    """
    Return ConfigParser object.
    If section_config passed then merges config and section_config
    into one ConfigParser instance.

    Args:
        config: Path to .ini or .json configuration file.
        section_config (str): File or URL to obtain additional configuration sections.
                              Default value is None.
        timeout: Number of seconds to wait for response for each HTTP request.
    """
    try:
        conf_path = Path(config)

        if section_config and conf_path.suffix != ".json":
            raise Exception(
                f"Config '{config}' extension must be '.json' to also use "
                f"optional section config '{section_config}'"
            )
        elif conf_path.suffix == ".json":
            config_parser = get_json_config_parser(conf_path)
            if section_config:
                section_parser = get_json_section_config_parser(section_config, timeout)
                config_parser = merge_config_parsers(config_parser, section_parser)
        else:  # pragma: no cover
            config_parser = configparser.ConfigParser()
            conf = config_parser.read(conf_path)
            if not conf:
                raise Exception(f"File '{config}' not found")

        if len(config_parser.sections()) < 1:  # pragma: no cover
            raise Exception(f"File '{config}' does not have any sections")

        return config_parser

    except Exception as e:  # pragma: no cover
        raise Exception(e)


class LogConfigModel(BaseModel):
    """
    Class with required log config values and their types.
    """

    log_when: str
    log_interval: PositiveInt
    log_backup_count: NonNegativeInt


def validate_log_config(
    config_parser: configparser.ConfigParser,
) -> LogConfigModel:
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
            "log_interval": config_parser.getint(
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


def validate_min_size_kb(config_parser: configparser.ConfigParser) -> int:
    """
    Return min_size_kb from config as integer.

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
                "Value for config value 'min_size_kb' must be greater than or equal "
                "to 0"
            )
    except ValidationError as e:
        raise Exception(f"Failed to validate config value 'min_size_kb, error(s): {e}")
    except ValueError as e:  # pragma: no cover
        raise Exception(
            f"Incorrect value for config value 'min_size_kb', error(s): {e}"
        )
    except Exception as e:  # pragma: no cover
        raise Exception(f"{e}")


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


def validate_s3_config() -> S3ConfigModel:
    """
    Return S3ConfigModel object after validating required environment variables.
    """
    try:
        load_dotenv()
        s3_conf = {
            "endpoint_url": os.getenv("ENDPOINT_URL"),
            "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        }
        return S3ConfigModel(**s3_conf)
    except ValidationError as e:
        raise Exception(
            f"Failed to validate S3 config environment variables, error(s): {e}"
        )
    except Exception as e:  # pragma: no cover
        raise Exception(e)


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
    except Exception as e:
        return Exception(f"{e}")
