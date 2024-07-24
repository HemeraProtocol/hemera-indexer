import ast
import os
import sys
from importlib import import_module
from typing import Type, List


def import_string(dotted_path: str):
    """
    Import a dotted module path and return the attribute/class designated by the last name in the path.

    Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError:
        raise ImportError(f"{dotted_path} doesn't look like a module path")

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError:
        raise ImportError(f'Module "{module_path}" does not define a "{class_name}" attribute/class')


def get_all_subclasses(base_class: Type[object], directory) -> List[object]:
    subclasses = []
    for dir_path, dir_names, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith(".py") and filename != "__init__.py":
                file_path = os.path.join(dir_path, filename)
                with open(file_path, "r", encoding="utf-8") as file:
                    file_content = file.read()

                parsed_content = ast.parse(file_content)
                class_names = [node.name for node in ast.walk(parsed_content) if isinstance(node, ast.ClassDef)]

                for cls in class_names:
                    full_class_path = os.path.join(file_path[:-3], cls)
                    dot_path = full_class_path.replace(os.path.sep, ".")

                    # may accrue circular dependency error
                    try:
                        subclass = import_string(dot_path)
                    except ImportError as e:
                        continue

                    if issubclass(subclass, base_class) and subclass is not base_class:
                        subclasses.append(subclass)

                    if full_class_path in sys.modules:
                        del sys.modules[full_class_path]

    return subclasses
