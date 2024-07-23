import os
import ast
from datetime import datetime, timezone
from typing import Type

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import BYTEA, TIMESTAMP

from common.services.sqlalchemy_session import RouteSQLAlchemy
from common.utils.module_loading import import_string
from indexer.domain import Domain

db = RouteSQLAlchemy(session_options={"autoflush": False})


class HemeraModel(db.Model):
    __abstract__ = True

    def model_domain_mapping(self):
        pass

    def converter(self, data: Type[Domain], is_update=False):
        converted_data = {}
        for key in data.__dict__.keys():
            if key in self.__table__.c:
                column_type = self.get_column_type(key)
                if isinstance(column_type, BYTEA):
                    converted_data[key] = bytes.fromhex(getattr(data, key)[2:])
                elif isinstance(column_type, TIMESTAMP):
                    converted_data[key] = func.to_timestamp(getattr(data, key))
                else:
                    converted_data[key] = getattr(data, key)

        if is_update:
            converted_data['update_time'] = func.to_timestamp(int(datetime.now(timezone.utc).timestamp()))

        if 'reorg' in self.__table__.columns:
            converted_data['reorg'] = False

        return converted_data

    def get_column_type(self, column_name):
        return self.__table__.c[column_name].type


def import_all_models():
    for name in __lazy_imports:
        __getattr__(name)


def __getattr__(name):
    if name != "ImportError":
        path = __lazy_imports.get(name)
        if not path:
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

        val = import_string(f"{path}.{name}")

    # Store for next time
    globals()[name] = val
    return val


def scan_modules(directory):
    modules = {}
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") and file != "__init__.py" and file != "bridge.py":
                module_file_path = os.path.join(directory, file)
                module_path = module_file_path.replace(os.path.sep, ".")
                with open(module_file_path, "r", encoding="utf-8") as module:
                    file_content = module.read()

                parsed_content = ast.parse(file_content)
                class_names = [node.name for node in ast.walk(parsed_content) if isinstance(node, ast.ClassDef)]
                for cls in class_names:
                    modules[cls] = module_path[:-3]
    return modules


__lazy_imports = scan_modules("common/models")
