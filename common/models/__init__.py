import glob
import os
import ast
from datetime import datetime, timezone
from typing import Type

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import BYTEA, TIMESTAMP, ARRAY

from common.services.sqlalchemy_session import RouteSQLAlchemy
from common.utils.module_loading import import_string
from indexer.domain import Domain

model_path_patterns = ['common/models', 'indexer/modules/*/models', 'indexer/modules/custom/*/models']

# db = RouteSQLAlchemy(session_options={"autoflush": False})
db = SQLAlchemy(session_options={"autoflush": False})


class HemeraModel(db.Model):
    __abstract__ = True

    @staticmethod
    def model_domain_mapping():
        pass


def get_column_type(table: Type[HemeraModel], column_name):
    return table.__table__.c[column_name].type


def general_converter(table: Type[HemeraModel], data: Domain, is_update=False):
    converted_data = {}
    for key in data.__dict__.keys():
        if key in table.__table__.c:
            column_type = get_column_type(table, key)
            if isinstance(column_type, BYTEA) and not isinstance(getattr(data, key), bytes):
                converted_data[key] = bytes.fromhex(getattr(data, key)[2:]) if getattr(data, key) else None
            elif isinstance(column_type, TIMESTAMP):
                converted_data[key] = func.to_timestamp(getattr(data, key))
            elif isinstance(column_type, ARRAY) and isinstance(column_type.item_type, BYTEA):
                converted_data[key] = [bytes.fromhex(address[2:]) for address in getattr(data, key)]
            else:
                converted_data[key] = getattr(data, key)

    if is_update:
        converted_data['update_time'] = func.to_timestamp(int(datetime.now(timezone.utc).timestamp()))

    if 'reorg' in table.__table__.columns:
        converted_data['reorg'] = False

    return converted_data


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


def scan_modules():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
    modules = {}

    for model_pattern in model_path_patterns:
        pattern_path = os.path.join(project_root, model_pattern)
        for models_dir in glob.glob(pattern_path):
            if os.path.isdir(models_dir):
                for file in os.listdir(models_dir):
                    if file.endswith('.py') and file != "__init__.py":
                        module_file_path = os.path.join(models_dir, file)
                        module_relative_path = os.path.relpath(module_file_path, start=project_root)
                        module_import_path = module_relative_path.replace(os.path.sep, '.')

                        with open(module_file_path, "r", encoding="utf-8") as module:
                            file_content = module.read()

                        parsed_content = ast.parse(file_content)
                        class_names = [node.name for node in ast.walk(parsed_content) if isinstance(node, ast.ClassDef)]
                        for cls in class_names:
                            modules[cls] = module_import_path[:-3]

    return modules


__lazy_imports = scan_modules()
# __lazy_imports = scan_modules("common/models")
