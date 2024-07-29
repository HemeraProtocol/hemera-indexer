from dataclasses import asdict, is_dataclass, dataclass, fields
from typing import Dict, Any, get_origin, Union, get_args

from common.utils.format_utils import to_snake_case


@dataclass
class Domain(object):

    def __repr__(self):
        return dataclass_to_dict(self)

    @classmethod
    def type(cls) -> str:
        """Return the class name in snake_case."""
        return to_snake_case(cls.__name__)

    def dict_to_entity(self, data_dict: Dict[str, Any]):
        valid_keys = {field.name for field in fields(self.__class__)}
        filtered_data = {k: v for k, v in data_dict.items() if k in valid_keys}

        for key, value in filtered_data.items():
            setattr(self, key, value)

    @classmethod
    def is_filter_data(cls):
        return False


@dataclass
class FilterData(Domain):

    @classmethod
    def is_filter_data(cls):
        return True


def dict_to_dataclass(data: Dict[str, Any], cls):
    """
    Converts a dictionary to a dataclass instance, handling nested structures.

    Args:
        data (Dict[str, Any]): The input dictionary.
        cls: The dataclass type to convert to.

    Returns:
        An instance of the specified dataclass.
    """
    fieldtypes = {f.name: f.type for f in cls.__dataclass_fields__.values()}
    init_values = {}
    for field, field_type in fieldtypes.items():
        if field in data:
            origin = get_origin(field_type)
            args = get_args(field_type)
            if origin is list:
                # Handle lists
                item_type = args[0]
                init_values[field] = [
                    dict_to_dataclass(item, item_type) if isinstance(item, dict) else item for item in data[field]
                ]
            elif hasattr(field_type, "__dataclass_fields__"):
                # Handle nested dataclass
                init_values[field] = dict_to_dataclass(data[field], field_type)
            else:
                init_values[field] = data[field]
        else:
            if get_origin(field_type) is Union and type(None) in get_args(field_type):
                init_values[field] = None
            else:
                init_values[field] = field_type()
    return cls(**init_values)


def dataclass_to_dict(instance: Domain) -> Dict[str, Any]:
    if not is_dataclass(instance):
        raise ValueError("dataclass_to_dict() should be called on dataclass instances only.")

    result = asdict(instance)
    result["item"] = instance.type()

    for key, value in result.items():
        if isinstance(value, list):
            result[key] = [dataclass_to_dict(item) if is_dataclass(item) else item for item in value]
        elif is_dataclass(value):
            result[key] = dataclass_to_dict(value)

    return result
