import logging
import os


def check_and_set_default_env(key: str, default_value: str):
    env_value = os.environ.get(key)
    if env_value is None:
        os.environ[key] = default_value
    else:
        logging.warning(
            f"The environment variable: {key} has been set to `{env_value}`. "
            f"Please confirm that {key} assignment meets your expectations."
        )
