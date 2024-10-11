import re
from datetime import datetime
from decimal import Decimal
from typing import Optional, Union


def bytes_to_hex_str(b: bytes) -> str:
    return "0x" + b.hex()


def hex_str_to_bytes(h: str) -> bytes:
    if not h:
        return None
    if h.startswith("0x"):
        return bytes.fromhex(h[2:])
    return bytes.fromhex(h)


def to_int_or_none(val):
    if isinstance(val, int):
        return val
    if val is None or val == "":
        return None
    try:
        return int(val)
    except ValueError:
        return None


def to_float_or_none(val):
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
                json_data[c.name] = bytes_to_hex_str(attr)
            else:
                json_data[c.name] = attr
    return json_data


def row_to_dict(row):
    return {key: format_value_for_json(value) for key, value in row._asdict().items()}


def format_block_id(block_id: Union[Optional[int], str]) -> str:
    return hex(block_id) if block_id and isinstance(block_id, int) else block_id


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
        return bytes_to_hex_str(value)
    elif isinstance(value, list):
        return [format_value_for_json(v) for v in value]
    elif isinstance(value, dict):
        return {k: format_value_for_json(v) for k, v in value.items()}
    else:
        return value
