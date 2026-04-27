"""Config utilities, parses and validates config .ini files."""

import configparser
import json
from pathlib import Path
import requests
from websnap.session import make_session
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
from websnap.constants import LogRotation, MIN_SIZE_KB, TIMEOUT


_ta = TypeAdapter(PositiveInt)


def validate_timeout(timeout: int) -> None:
    """
    Validate that timeout is a positive integer.
    Raises ValueError if validation fails.

    Args:
        timeout: Number of seconds to wait for response for each HTTP request.
    """
    try:
        _ta.validate_python(timeout)
    except (ValueError, ValidationError):
        raise ValueError(f"'timeout' is not a positive integer: {timeout}")


def validate_backup_s3_count(backup_s3_count: int | None) -> None:
    """
    Validate that backup_s3_count is a positive integer if provided.
    None values are allowed (validation passes).
    Raises ValueError if validation fails.

    Args:
        backup_s3_count: Number of times to copy and backup S3 objects.
    """
    if backup_s3_count is not None:
        try:
            _ta.validate_python(backup_s3_count)
        except (ValueError, ValidationError):
            raise ValueError(
                f"'backup_s3_count' is not a positive integer: {backup_s3_count}"
            )


def validate_endpoint_url(endpoint_url: str | None, s3_uploader: bool) -> str:
    """
    Validate and return endpoint_url, it must be truthy and an http or https URL.
    If validation fails then raises Exception.
    """
    if s3_uploader and not endpoint_url:
        raise ValueError(
            "'--endpoint-url' option (endpoint_url function argument) "
            "must be provided when the "
            "'--s3-uploader' option (s3_uploader function argument) "
            "is enabled (set to True)"
        )

    if endpoint_url:
        try:
            ta = TypeAdapter(AnyHttpUrl)
            validated = ta.validate_python(endpoint_url)
            return str(validated)

        except ValidationError:
            raise ValueError(
                f"'--endpoint-url' value (endpoint_url function argument) "
                f"'{endpoint_url}' "
                f"is not a valid HTTP/HTTPS URL"
            )

    return endpoint_url


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
        raise FileNotFoundError(f"File '{config_path}' not found")
    except json.JSONDecodeError as e:
        raise ValueError(f"File '{config_path}' is not valid JSON: {e}")


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
        response = make_session().get(config_url, timeout=timeout)

        response.raise_for_status()

        data = response.json()

        config_parser = configparser.ConfigParser()
        config_parser.read_dict(data)

        return config_parser

    except requests.exceptions.Timeout:
        raise TimeoutError(f"URL {config_url} timed out after {timeout}s")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(
            f"URL {config_url} failed with status: {e.response.status_code}"
        )
    except json.JSONDecodeError:
        raise ValueError(f"URL {config_url} did not return valid JSON")
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"A network error occurred: {e}")


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
    if is_url(section_config):
        section_parser = get_url_json_config_parser(section_config, timeout)
    else:
        if (section_path := Path(section_config)).suffix == ".json":
            section_parser = get_json_config_parser(section_path)
        else:
            raise ValueError("Section config extension must be '.json'")

    if not isinstance(section_parser, configparser.ConfigParser):
        raise TypeError(f"Expected ConfigParser, got {type(section_parser).__name__}")

    if section_parser.defaults():
        raise ValueError("Section config cannot have a 'DEFAULT' section")

    return section_parser


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
    conf_path = Path(config)

    if section_config and conf_path.suffix != ".json":
        raise ValueError(
            f"Config '{config}' extension must be '.json' to also use "
            f"optional section config '{section_config}'"
        )
    elif conf_path.suffix == ".json":
        config_parser = get_json_config_parser(conf_path)
        if section_config:
            section_parser = get_json_section_config_parser(section_config, timeout)
            config_parser = merge_config_parsers(config_parser, section_parser)
    else:
        config_parser = configparser.ConfigParser()
        conf = config_parser.read(conf_path)
        if not conf:
            raise FileNotFoundError(f"File '{config}' not found")

    if len(config_parser.sections()) < 1:
        raise ValueError(f"File '{config}' does not have any sections")

    return config_parser


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
        raise ValueError(f"Log configuration is invalid: {e}")
    except ValueError as e:
        raise ValueError(f"Incorrect log related value in config: {e}")


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

    except ValueError as e:
        raise ValueError(f"Incorrect value for config value 'min_size_kb': {e}")


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
    Raises ValidationError if parsing fails.

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
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        raise ValueError(f"Missing required key in section '{section}': {e}")
    except ValidationError as e:
        raise ValueError(f"Failed to validate config section '{section}': {e}")


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
    Raises ValueError if parsing fails or config is invalid.

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
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        raise ValueError(f"Missing required key in S3 config section '{section}': {e}")
    except (ValidationError, ValueError) as e:
        raise ValueError(f"Failed to validate S3 config section '{section}': {e}")
