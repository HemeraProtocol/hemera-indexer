import re
from datetime import datetime
from decimal import Decimal
from typing import Optional, Union

from sqlalchemy import Integer, Numeric


def bytes_to_hex_str(b: bytes) -> Optional[str]:
    """
    Converts a bytes object to a hexadecimal string with '0x' prefix.

    param b: The bytes object to convert.
    :type b: bytes

    :return: A hexadecimal string representation of the input bytes.
    :rtype: str
    """
    if not b:
        return None
    return "0x" + b.hex()


def hex_str_to_bytes(h: str) -> Optional[bytes]:
    """
    Converts a hexadecimal string to a bytes object.

    :param h: The hexadecimal string to convert, with or without '0x' prefix.
    :type h: str

    :return: A bytes object representing the input hex string, or None if input is empty.
    :rtype: Optional[bytes]
    """
    if not h:
        return None
    if h.startswith("0x"):
        return bytes.fromhex(h[2:])
    return bytes.fromhex(h)


def to_int_or_none(val):
    """
    Attempts to convert a value to an integer, returning None if not possible.

    :param val: The value to convert.
    :type val: Any

    :return: The integer value if conversion is successful, None otherwise.
    :rtype: Optional[int]
    """
    if isinstance(val, int):
        return val
    if val is None or val == "":
        return None
    try:
        return int(val)
    except ValueError:
        return None


def to_float_or_none(val):
    """
    Attempts to convert a value to a float, returning None if not possible.

    :param val: The value to convert.
    :type val: Any

    :return: The float value if conversion is successful, None if conversion fails
    or the original value if it can't be cast to float.
    :rtype: Optional[float]
    """
    if isinstance(val, float):
        return val
    if val is None or val == "":
        return None
    try:
        return float(val)
    except ValueError:
        print("can't cast %s to float" % val)
        return val


def to_snake_case(name: str) -> str:
    """
    Converts a CamelCase string to snake_case.

    :param name: The CamelCase string to convert.
    :type name: str

    :return: The converted snake_case string.
    :rtype: str
    """
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def to_camel_case(name: str) -> str:
    """
    Converts a snake_case string to CamelCase.

    :param name: The snake_case string to convert.
    :type name: str

    :return: The converted CamelCase string.
    :rtype: str
    """
    components = name.split("_")
    return "".join(x.title() for x in components)


def to_space_camel_case(name: str) -> str:
    """
    Converts a snake_case string to CamelCase.

    :param name: The snake_case string to convert.
    :type name: str

    :return: The converted CamelCase string.
    :rtype: str
    """
    components = name.split("_")
    return " ".join(x.title() for x in components)


def as_dict(self):
    """
    Converts an SQLAlchemy model instance to a dictionary.
    This method handles special cases like datetime, Decimal, and bytes objects.
    It also processes the 'meta_data' column if present.

    :param self: The SQLAlchemy model instance.

    :return: A dictionary representation of the model instance.
    :rtype: Dict[str, Any]
    """
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
                if isinstance(c.type, (Numeric, Integer)):
                    if c.type.scale == 0 or (isinstance(c.type, Numeric) and c.type.scale is None):
                        # Additional check to ensure the value is actually an integer
                        if attr.as_tuple().exponent >= 0:
                            json_data[c.name] = int(attr)
                        else:
                            json_data[c.name] = float(attr)
                    else:
                        json_data[c.name] = float(attr)
                else:
                    json_data[c.name] = float(attr)
            elif isinstance(attr, bytes):
                json_data[c.name] = bytes_to_hex_str(attr)
            else:
                json_data[c.name] = attr
    return json_data


def row_to_dict(row):
    """
    Converts a database row to a dictionary, formatting values for JSON serialization.

    :param row: The database row to convert.

    :return: A dictionary representation of the row with formatted values.
    :rtype: Dict[str, Any]
    """
    return {key: format_value_for_json(value) for key, value in row._asdict().items()}


def format_block_id(block_id: Union[Optional[int], str]) -> str:
    """
    Formats a block ID to a hexadecimal string if it's an integer.

    :param block_id: The block ID to format.
    :type block_id: Union[Optional[int], str]

    :return: The formatted block ID.
    :rtype: str
    """
    return hex(block_id) if block_id and isinstance(block_id, int) else block_id


def format_to_dict(row):
    """
    Formats various types of database results to a dictionary.
    This function can handle None, named tuples, SQLAlchemy model instances, and other types.

    :param row: The database result to format.
    :type row: Any

    :return: A dictionary representation of the input, or None if input is None.
    :rtype: Optional[Dict[str, Any]]
    """
    if row is None:
        return None
    if hasattr(row, "_asdict"):
        return row_to_dict(row)
    elif hasattr(row, "__table__"):
        return as_dict(row)
    else:
        return format_value_for_json(row)


def format_value_for_json(value):
    """
    Formats a value for JSON serialization.
    Handles special cases like datetime, Decimal, bytes, lists, and dictionaries.

    :param value: The value to format.
    :type value: Any

    :return: The formatted value suitable for JSON serialization.
    :rtype: Any
    """

    if isinstance(value, datetime):
        return value.astimezone().isoformat("T", "seconds")
    elif isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, bytes):
        return bytes_to_hex_str(value)
    elif isinstance(value, list):
        return [format_value_for_json(v) for v in value]
    elif isinstance(value, dict):
        return {k: format_value_for_json(v) for k, v in value.items()}
    else:
        return value


def convert_dict(input_item):
    """
    Recursively converts a dictionary or list to a specific structure.
    Each key-value pair in dictionaries is converted to a list of dictionaries
    with 'name', 'value', and 'type' keys.

    :param input_item: The item to convert.
    :type input_item: Any

    :return: The converted structure.
    :rtype: Any
    """
    if isinstance(input_item, dict):
        result = []
        for key, value in input_item.items():
            entry = {"name": key, "value": None, "type": None}
            if isinstance(value, (list, tuple, set)):
                entry["type"] = "list"
                entry["value"] = convert_dict(value)
            elif isinstance(value, dict):
                entry["type"] = "list"
                entry["value"] = convert_dict(value)
            elif isinstance(value, str):
                entry["type"] = "string"
                entry["value"] = value
            elif isinstance(value, int):
                entry["type"] = "int"
                entry["value"] = value
            else:
                entry["type"] = "unknown"
                entry["value"] = value

            result.append(entry)
        return result

    elif isinstance(input_item, (list, tuple, set)):
        return [convert_dict(item) for item in input_item]

    return input_item


def convert_bytes_to_hex(item):
    """
    Recursively converts bytes objects to hexadecimal strings in complex data structures.
    This function can handle dictionaries, lists, tuples, and sets.

    :param item: The item to convert.
    :type item: Any

    :return: The converted item with bytes objects replaced by their hex representation.
    :rtype: Any
    """
    if isinstance(item, dict):
        return {key: convert_bytes_to_hex(value) for key, value in item.items()}
    elif isinstance(item, list):
        return [convert_bytes_to_hex(element) for element in item]
    elif isinstance(item, tuple):
        return tuple(convert_bytes_to_hex(element) for element in item)
    elif isinstance(item, set):
        return {convert_bytes_to_hex(element) for element in item}
    elif isinstance(item, bytes):
        return item.hex()
    else:
        return item
