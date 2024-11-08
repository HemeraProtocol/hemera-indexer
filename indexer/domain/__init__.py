import hashlib
import importlib
import inspect
import sys
from dataclasses import asdict, dataclass, fields, is_dataclass
from typing import Any, Dict, Union, get_args, get_origin

from common.utils.format_utils import to_snake_case
from common.utils.module_loading import import_string, scan_subclass_by_path_patterns

model_path_patterns = [
    "indexer/domain",
    "indexer/modules/*/domain",
    "indexer/modules/custom/*/domain",
]


class DomainMeta(type):
    _registry = {}
    _used_hash = set()
    _hash_mapping = {}
    _dataclass_mapping = {}
    _code_integrity = {}

    @classmethod
    def _generate_code(mcs, cls) -> str:
        cut = len(cls.__name__) % 32 // 2
        salt = hashlib.sha1(cls.__name__.encode("utf-8")).hexdigest()
        hash_value = hashlib.sha256(f"{cls.__name__}{salt[cut:cut + 10]}".encode("utf-8")).hexdigest()

        code = hash_value[cut : cut + 8]

        if code in mcs._used_hash:
            existing_domain = mcs._hash_mapping[code]
            raise ValueError(
                f"\nHash collision detected!\n"
                f"Generated hash '{code}' for '{cls.__module__}.{cls.__name__}'\n"
                f"conflicts with existing domain '{existing_domain}'.\n"
                f"Please manually specify a different hash code using:\n"
                f"class {cls.__name__}(Domain):\n"
                f"    __manual_hash__ = 'xxxxxxxx'  # Replace with a unique 8-character code"
            )

        return code

    def __new__(mcs, name, bases, attrs):
        new_cls = super().__new__(mcs, name, bases, attrs)

        if name == "Domain":
            return new_cls

        manual_hash = attrs.get("__manual_hash__")

        if manual_hash:
            if manual_hash in mcs._used_hash:
                existing_domain = mcs._hash_mapping[manual_hash]

                raise ValueError(
                    f"\nHash collision detected!\n"
                    f"Generated hash '{manual_hash}' for '{new_cls.__module__}.{name}'\n"
                    f"conflicts with existing domain '{existing_domain}'.\n"
                    f"Please manually specify a different hash code using:\n"
                    f"class {new_cls.__name__}(Domain):\n"
                    f"    __manual_hash__ = 'xxxxxxxx'  # Replace with a unique 8-character code"
                )
            dataclass_code = manual_hash
        else:
            dataclass_code = mcs._generate_code(new_cls)

        module = sys.modules.get(new_cls.__module__) or importlib.import_module(new_cls.__module__)
        code_hash = hashlib.sha256(inspect.getsource(module).encode("utf-8")).hexdigest()

        mcs._used_hash.add(dataclass_code)
        mcs._hash_mapping[dataclass_code] = f"{new_cls.__module__}.{name}"
        mcs._dataclass_mapping[f"{new_cls.__module__}.{name}"] = dataclass_code
        mcs._code_integrity[dataclass_code] = code_hash
        setattr(new_cls, "_auto_hash", dataclass_code)

        return new_cls

    @classmethod
    def get_all_subclasses_with_type(mcs):
        def get_subclasses(cls):
            subclasses = set()
            for subclaz in cls.__subclasses__():
                subclasses.add(subclaz)
                subclasses.update(get_subclasses(subclaz))
            return subclasses

        all_subclasses = get_subclasses(Domain)

        subclasses_dict = {}
        for subclass in all_subclasses:
            if hasattr(subclass, "type") and subclass.type() not in subclasses_dict:
                subclasses_dict[subclass.type()] = subclass
            elif hasattr(subclass, "type") and subclass.type() in subclasses_dict:
                raise TypeError(f"Type {subclass} has name conflict with type {subclasses_dict[subclass.type()]}!")
        return subclasses_dict


@dataclass
class Domain(metaclass=DomainMeta):
    __manual_hash__ = None

    def __init__(self):
        self._auto_hash = None

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

    @classmethod
    def is_filter_data(cls):
        return False

    @classmethod
    def get_code_hash(cls):
        return cls._auto_hash


@dataclass
class FilterData(Domain):

    @classmethod
    def is_filter_data(cls):
        return True


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
    for domain in __domain_imports.keys():
        mapping[to_snake_case(domain)] = import_string(__domain_imports[domain])

    return mapping


__domain_imports = {
    k: v["cls_import_path"] for k, v in scan_subclass_by_path_patterns(model_path_patterns, Domain).items()
}
domains_mapping = generate_domains_mapping()
