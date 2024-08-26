import ast
import glob
import os
from datetime import datetime, timezone
from typing import Type

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import ARRAY, BYTEA, TIMESTAMP

from common.services.sqlalchemy_session import RouteSQLAlchemy
from common.utils.module_loading import import_string, scan_subclass_by_path_patterns
from indexer.domain import Domain

model_path_patterns = [
    "common/models",
    "indexer/modules/*/models",
    "indexer/modules/custom/*/models",
    "indexer/aggr_jobs/*/models",
]

# db = RouteSQLAlchemy(session_options={"autoflush": False})
db = SQLAlchemy(session_options={"autoflush": False})


class HemeraModel(db.Model):
    __abstract__ = True

    @staticmethod
    def model_domain_mapping():
        pass

    @classmethod
    def schema(self):
        return "public"


def get_column_type(table: Type[HemeraModel], column_name):
    return table.__table__.c[column_name].type


def general_converter(table: Type[HemeraModel], data: Domain, is_update=False):
    converted_data = {}
    for key in data.__dict__.keys():
        if key in table.__table__.c:
            column_type = get_column_type(table, key)
            if isinstance(column_type, BYTEA) and not isinstance(getattr(data, key), bytes):
                if isinstance(getattr(data, key), str):
                    converted_data[key] = bytes.fromhex(getattr(data, key)[2:]) if getattr(data, key) else None
                elif isinstance(getattr(data, key), int):
                    converted_data[key] = getattr(data, key).to_bytes(32, byteorder="big")
                else:
                    converted_data[key] = None
            elif isinstance(column_type, TIMESTAMP):
                converted_data[key] = datetime.utcfromtimestamp(getattr(data, key))
            elif isinstance(column_type, ARRAY) and isinstance(column_type.item_type, BYTEA):
                converted_data[key] = [bytes.fromhex(address[2:]) for address in getattr(data, key)]
            else:
                converted_data[key] = getattr(data, key)

    if is_update:
        converted_data["update_time"] = datetime.utcfromtimestamp(datetime.now(timezone.utc).timestamp())

    if "reorg" in table.__table__.columns:
        converted_data["reorg"] = False

    return converted_data


def import_all_models():
    for name in __models_imports:
        __getattr__(name)


def __getattr__(name):
    if name != "ImportError":
        path = __models_imports.get(name)
        if not path:
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

        val = import_string(f"{path}.{name}")

    # Store for next time
    globals()[name] = val
    return val


__models_imports = {
    k: v["module_import_path"] for k, v in scan_subclass_by_path_patterns(model_path_patterns, HemeraModel).items()
}
