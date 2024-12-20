import ast
import glob
import logging
import os
import pkgutil
from importlib import import_module
from typing import Dict, List, Type

from hemera.common.utils.file_utils import get_project_root


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


def scan_subclass_by_path_patterns(
    path_patterns: List[str], base_class: Type[object], exclude_path=[]
) -> Dict[str, dict]:
    project_root = get_project_root()
    exclude_path = [os.path.join(project_root, path) for path in exclude_path]

    mapping = {}
    for model_pattern in path_patterns:
        pattern_path = os.path.join(project_root, model_pattern)
        for models_dir in glob.glob(pattern_path):
            if os.path.isdir(models_dir) and models_dir not in exclude_path:
                for file in os.listdir(models_dir):
                    if file.endswith(".py") and file != "__init__.py":
                        module_file_path = os.path.join(models_dir, file)
                        module_relative_path = os.path.relpath(module_file_path, start=project_root)
                        module_import_path = module_relative_path.replace(os.path.sep, ".")

                        with open(module_file_path, "r", encoding="utf-8") as module:
                            file_content = module.read()

                        parsed_content = ast.parse(file_content)
                        class_names = [node.name for node in ast.walk(parsed_content) if isinstance(node, ast.ClassDef)]

                        for cls in class_names:
                            full_class_path = os.path.join(module_import_path[:-3], cls)
                            dot_path = full_class_path.replace(os.path.sep, ".")
                            module = import_string(dot_path)

                            if not issubclass(module, base_class):
                                continue
                            mapping[cls] = {
                                "module_import_path": module_import_path[:-3],
                                "cls_import_path": f"{module_import_path[:-3]}.{cls}",
                            }

    return mapping


def get_all_subclasses(base_class):
    subclasses = []

    def recurse(cls):
        for subclass in cls.__subclasses__():
            if subclass not in subclasses:
                subclasses.append(subclass)
                recurse(subclass)

    recurse(base_class)
    return subclasses


def import_submodules(package_name):
    try:
        package = import_module(package_name)
    except ImportError:
        logging.warn(f"Failed to import {package_name}")
        return
    for _, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + "." + name
        import_module(full_name)
        if is_pkg:
            import_submodules(full_name)
