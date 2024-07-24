import os
from configparser import ConfigParser

from sqlalchemy.engine import make_url

from api.app.config import AppConfig

_config_instance = None
_is_initialized = False

config_path = "resource/hemera.ini"


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
    app_config = None
    try:
        if os.path.exists(config_path):
            config.read(config_path)
            app_config = AppConfig.load_from_config_file(config)
    except FileNotFoundError:
        print("Cannot find config file.")
        exit()

    return app_config


def set_config_value(config_file, section, key, value):
    config = ConfigParser()
    config.read(config_file)
    config[section][key] = value

    with open(config_file, 'w') as configfile:
        config.write(configfile)


def read_config_value(config_file, section, key):
    config = ConfigParser()
    try:
        config.read(config_file)
        value = config[section][key]
    except Exception as e:
        value = None

    return value


def init_config_setting(db_url, rpc_endpoint):
    parsed_url = make_url(db_url)

    username = parsed_url.username
    password = parsed_url.password
    hostname = parsed_url.host
    port = parsed_url.port
    database = parsed_url.database

    set_config_value(config_path, section='alembic', key='sqlalchemy.url', value=db_url)
    set_config_value(config_path, section='DB_CREDS', key='HOST', value=hostname)
    set_config_value(config_path, section='DB_CREDS', key='COMMON_HOST', value=hostname)
    set_config_value(config_path, section='DB_CREDS', key='WRITE_HOST', value=hostname)
    set_config_value(config_path, section='DB_CREDS', key='PORT', value=str(port))
    set_config_value(config_path, section='DB_CREDS', key='USER', value=username)
    set_config_value(config_path, section='DB_CREDS', key='PASSWD', value=password)
    set_config_value(config_path, section='DB_CREDS', key='DB_NAME', value=database)
    set_config_value(config_path, section='BLOCK_CHAIN', key='RPC_ENDPOINT', value=rpc_endpoint)
