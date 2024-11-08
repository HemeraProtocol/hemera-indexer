import logging
import os
from configparser import ConfigParser

from api.app.config import AppConfig

_config_instance = None
_is_initialized = False


def get_config():
    global _config_instance
    if _config_instance is None:
        _config_instance = read_config()
    return _config_instance


def set_config(config: AppConfig):
    global _config_instance, _is_initialized
    if not _is_initialized:
        _config_instance = config
        _is_initialized = True
    else:
        if config.env != "ut":
            raise Exception("Configuration can only be set once.")
        else:
            _config_instance = config


def read_config():
    config = ConfigParser()
    try:
        if os.path.exists("api_config.conf"):
            config.read("api_config.conf")
            app_config = AppConfig.load_from_config_file(config)
        elif os.path.exists("api_config.yaml"):
            app_config = AppConfig.load_from_yaml_file("api_config.yaml")
        else:
            app_config = AppConfig()
        app_config.update_from_env()
    except Exception as e:
        logging.error("Error initializing config")
        exit()

    return app_config


def set_config_value(config_file, section, key, value):
    config = ConfigParser()
    config.read(config_file)
    config[section][key] = value

    with open(config_file, "w") as configfile:
        config.write(configfile)


def read_config_value(config_file, section, key):
    config = ConfigParser()
    try:
        config.read(config_file)
        value = config[section][key]
    except Exception as e:
        value = None

    return value
