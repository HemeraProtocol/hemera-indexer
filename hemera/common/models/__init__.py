from dataclasses import fields
from datetime import datetime, timezone
from typing import Any, Dict, Set, Type

from psycopg2._json import Json
from sqlalchemy import NUMERIC as SQL_NUMERIC
from sqlalchemy import DateTime, LargeBinary
from sqlalchemy import Numeric
from sqlalchemy import Numeric as SQL_Numeric
from sqlalchemy.dialects.postgresql import ARRAY, BYTEA, JSON, JSONB, NUMERIC, TIMESTAMP
from sqlmodel import SQLModel

from hemera.common.utils.format_utils import hex_str_to_bytes
from hemera.common.utils.module_loading import import_string, import_submodules
from hemera.indexer.domains import Domain


class HemeraMeta(type(SQLModel)):
    _registry: Dict[str, Type["HemeraModel"]] = {}

    def __new__(mcs, name, bases, attrs, **kwargs):
        new_cls = super().__new__(mcs, name, bases, attrs, **kwargs)
        if name != "HemeraModel" and issubclass(new_cls, HemeraModel):
            mcs._registry[name] = new_cls

        return new_cls

    @classmethod
    def get_all_subclasses(mcs) -> Dict[Type["HemeraModel"], Type["HemeraModel"]]:
        import_submodules("hemera.common.models")

        def get_subclasses(cls) -> Set[Type["HemeraModel"]]:
            subclasses = set()
            for subclass in cls.__subclasses__():
                subclasses.add(subclass)
                subclasses.update(get_subclasses(subclass))
            return subclasses

        all_subclasses = get_subclasses(HemeraModel)
        return {subclass: subclass for subclass in all_subclasses}


class HemeraModel(SQLModel, metaclass=HemeraMeta):

    model_config = {"arbitrary_types_allowed": True}
    __query_order__: list = []

    @staticmethod
    def model_domain_mapping():
        pass

    @classmethod
    def get_all_annotation_keys(cls):
        keys = set()
        for clz in cls.__mro__:
            if "__annotations__" in clz.__dict__:
                keys.update(clz.__annotations__.keys())

        return keys

    @classmethod
    def get_all_hemera_model_dict(cls):
        return HemeraMeta.get_all_subclasses()

    def dict_to_entity(self, data_dict: Dict[str, Any]):
        valid_keys = {field.name for field in fields(self.__class__)}
        filtered_data = {k: v for k, v in data_dict.items() if k in valid_keys}

        for key, value in filtered_data.items():
            setattr(self, key, value)


def get_column_type(table: Type[HemeraModel], column_name):
    return table.__table__.c[column_name].type


def general_converter(table: Type[HemeraModel], data: Domain, is_update=False):
    converted_data = {}
    for key in data.__dict__.keys():
        if key in table.__table__.c:
            column_type = get_column_type(table, key)
            if (isinstance(column_type, BYTEA) or isinstance(column_type, LargeBinary)) and not isinstance(
                getattr(data, key), bytes
            ):
                if isinstance(getattr(data, key), str):
                    converted_data[key] = hex_str_to_bytes(getattr(data, key)) if getattr(data, key) else None
                elif isinstance(getattr(data, key), int):
                    converted_data[key] = getattr(data, key).to_bytes(32, byteorder="big")
                else:
                    converted_data[key] = None
            elif isinstance(column_type, TIMESTAMP) or isinstance(column_type, DateTime):
                converted_data[key] = datetime.utcfromtimestamp(getattr(data, key))
            elif isinstance(column_type, ARRAY) and isinstance(column_type.item_type, BYTEA):
                converted_data[key] = [hex_str_to_bytes(address) for address in getattr(data, key)]
            elif isinstance(column_type, JSONB) or isinstance(column_type, JSON) and getattr(data, key) is not None:
                converted_data[key] = Json(getattr(data, key))
            elif (
                isinstance(column_type, NUMERIC)
                or isinstance(column_type, SQL_NUMERIC)
                or isinstance(column_type, SQL_Numeric)
                or isinstance(column_type, Numeric)
            ) and isinstance(getattr(data, key), str):
                converted_data[key] = None
            else:
                converted_data[key] = getattr(data, key)

    if is_update:
        converted_data["update_time"] = datetime.utcfromtimestamp(datetime.now(timezone.utc).timestamp())

    if "reorg" in table.__table__.columns:
        converted_data["reorg"] = False

    return converted_data


def import_all_models():
    hemera_model_subclass = HemeraModel.get_all_subclasses()
    for name in hemera_model_subclass.keys():
        if name != "ImportError":
            path = hemera_model_subclass.get(name)
            if not path:
                raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

            val = import_string(f"{path}.{name}")

        # Store for next time
        globals()[name] = val
        return val
