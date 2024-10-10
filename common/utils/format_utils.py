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
