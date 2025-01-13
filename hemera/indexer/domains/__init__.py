from dataclasses import asdict, dataclass, fields, is_dataclass
from typing import Any, Dict, Union, get_args, get_origin

from hemera.common.utils.format_utils import to_snake_case
from hemera.common.utils.module_loading import import_string, scan_subclass_by_path_patterns


class DomainMeta(type):
    _registry = {}

    def __new__(mcs, name, bases, attrs):
        new_cls = super().__new__(mcs, name, bases, attrs)

        if name != "Domain" and issubclass(new_cls, Domain):
            mcs._registry[name] = new_cls

        return new_cls

    @classmethod
    def get_all_subclasses_with_type(mcs):
        def get_subclasses(cls):
            subclasses = set()
            for subclass in cls.__subclasses__():
                subclasses.add(subclass)
                subclasses.update(get_subclasses(subclass))
            return subclasses

        all_subclasses = get_subclasses(Domain)
        return {subclass.type(): subclass for subclass in all_subclasses if hasattr(subclass, "type")}


@dataclass
class Domain(metaclass=DomainMeta):

    def __repr__(self):
        return dataclass_to_dict(self)

    @classmethod
    def get_all_annotation_keys(cls):
        keys = set()
        for clz in cls.__mro__:
            if "__annotations__" in clz.__dict__:
                keys.update(clz.__annotations__.keys())

        return keys

    @classmethod
    def get_all_domain_dict(cls):
        return DomainMeta.get_all_subclasses_with_type()

    @classmethod
    def type(cls) -> str:
        """Return the class name in snake_case."""
        return to_snake_case(cls.__name__)

    def dict_to_entity(self, data_dict: Dict[str, Any]):
        valid_keys = {field.name for field in fields(self.__class__)}
        filtered_data = {k: v for k, v in data_dict.items() if k in valid_keys}

        for key, value in filtered_data.items():
            setattr(self, key, value)


from typing import Dict


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
                init_values[field] = (
                    [(dict_to_dataclass(item, item_type) if isinstance(item, dict) else item) for item in data[field]]
                    if data[field]
                    else []
                )
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


def generate_domains_mapping():
    mapping = {}
    for domain in DomainMeta.get_all_subclasses_with_type().keys():
        mapping[to_snake_case(domain)] = import_string(DomainMeta.get_all_subclasses_with_type()[domain])

    return mapping


domains_mapping = generate_domains_mapping()
