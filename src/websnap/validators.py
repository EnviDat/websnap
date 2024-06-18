"""Config utilities, parses and validates config .ini files."""

import configparser
from pathlib import Path
from pydantic import BaseModel, ValidationError


def get_config_parser(config_path: str) -> configparser.ConfigParser | None:
    """
    Return ConfigParser object. If ConfigParser object does not have any sections or
    raises and exception then returns None.

    Args:
        config_path (str): path to config .ini file
    """
    try:
        config_file = Path(config_path)
        config = configparser.ConfigParser()
        config.read(config_file)

        if not config:
            return None

        if len(config.sections()) < 1:
            print(
                f"ERROR: File '{config_path}' not valid config, "
                f"does not have any sections"
            )
            return None

        return config

    except FileNotFoundError:
        print(f"ERROR: Config file '{config_path}' not found")
        return None

    except Exception as e:
        print(f"ERROR: {e}")
        return None


class LogConfigModel(BaseModel):
    """
    Class with required log config values and their types.
    """

    log_when: str
    log_backup_count: int


def get_log_config(
    config_parser: configparser.ConfigParser,
) -> LogConfigModel | Exception:
    try:
        log = {
            "log_when": config_parser.get("DEFAULT", "log_when", fallback="midnight"),
            "log_backup_count": config_parser.getint(
                "DEFAULT", "log_backup_count", fallback=7
            ),
        }
        return LogConfigModel(**log)
    except ValidationError as e:
        raise Exception(f"Failed to validate config, error(s): {e}")
    except ValueError as e:
        raise Exception(f"Incorrect value used in config, error(s): {e}")
    except Exception as e:
        raise Exception(f"ERROR: {e}")
