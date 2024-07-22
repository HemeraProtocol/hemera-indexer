import os
import ast

from common.services.sqlalchemy_session import RouteSQLAlchemy
from common.utils.module_loading import import_string

db = RouteSQLAlchemy(session_options={"autoflush": False})


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
            if file.endswith(".py") and file != "__init__.py":
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
