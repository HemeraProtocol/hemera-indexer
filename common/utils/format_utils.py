import re
from datetime import datetime
from decimal import Decimal


def to_snake_case(name: str) -> str:
    """Convert a CamelCase name to snake_case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def as_dict(self):
    json_data = {}
    for c in self.__table__.columns:
        if c.name == "meta_data":
            meta_data_json = getattr(self, c.name)
            if meta_data_json:
                for key in meta_data_json:
                    json_data[key] = meta_data_json[key]
        else:
            attr = getattr(self, c.name)
            if isinstance(attr, datetime):
                json_data[c.name] = attr.astimezone().isoformat("T", "seconds")
            elif isinstance(attr, Decimal):
                json_data[c.name] = float(attr)
            elif isinstance(attr, bytes):
                json_data[c.name] = "0x" + attr.hex()
            else:
                json_data[c.name] = attr
    return json_data


def row_to_dict(row):
    return {key: format_value_for_json(value) for key, value in row._asdict().items()}


def format_to_dict(row):
    if row is None:
        return None
    if hasattr(row, "_asdict"):
        return row_to_dict(row)
    elif hasattr(row, "__table__"):
        return as_dict(row)
    else:
        return format_value_for_json(row)


def format_value_for_json(value):
    if isinstance(value, datetime):
        return value.astimezone().isoformat("T", "seconds")
    elif isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, bytes):
        return "0x" + value.hex()
    elif isinstance(value, list):
        return [format_value_for_json(v) for v in value]
    elif isinstance(value, dict):
        return {k: format_value_for_json(v) for k, v in value.items()}
    else:
        return value


def format_dollar_value(value: float) -> str:
    """ """
    if value > 1:
        return "{0:.2f}".format(value)
    return "{0:.6}".format(value)


def format_coin_value(value: int, decimal: int = 18) -> str:
    """
    Formats a given integer value into a string that represents a token value.
    Parameters:
        value (int): The value to be formatted

    Returns:
        str: The formatted token value as a string.
    """
    if value < 1000:
        return str(value)
    else:
        return "{0:.15f}".format(value / 10**18).rstrip("0").rstrip(".")


def format_coin_value_with_unit(value: int, native_token: str) -> str:
    """
    Formats a given integer value into a string that represents a token value with the appropriate unit.
    For values below 1000, it returns the value in WEI.
    For higher values, it converts the value to a floating-point representation in the native token unit,
    stripping unnecessary zeros.

    Parameters:
        value (int): The value to be formatted, typically representing a token amount in WEI.
        native_token (str):

    Returns:
        str: The formatted token value as a string with the appropriate unit.
    """
    if value < 1000:
        return str(value) + " WEI"
    else:
        return "{0:.15f}".format(value / 10**18).rstrip("0").rstrip(".") + " " + native_token


def hex_to_bytes(hex_value: str) -> bytes:
    return bytes.fromhex(hex_value[2:])
