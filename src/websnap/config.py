"""Config utilities, parses and validates config .ini files."""

import configparser
from pathlib import Path


def read_config(config_path: str) -> configparser.ConfigParser | None:
    """
    Return ConfigParser object. If ConfigParser object does not have any sections then
    returns None.

    Args:
        config_path (str): path to config INI file
    """
    try:
        with open(Path(config_path)) as conf_path:
            config = configparser.ConfigParser()
            config.read(conf_path)

        if config and len(config.sections()) < 1:
            return None

        return config

    except (FileNotFoundError, AttributeError) as e:
        print(f"ERROR: {e}")
        return None

    except Exception as e:
        print(f"EXCEPTION: {e}")
        return None
