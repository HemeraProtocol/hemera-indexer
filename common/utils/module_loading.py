import importlib.util
import os
import sys
from importlib import import_module


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



def get_all_subclasses(base_class, directory):
    subclasses = []

    def import_module(file_path):
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    def recurse(cls):
        for subclass in cls.__subclasses__():
            if subclass not in subclasses:
                subclasses.append(subclass)
                recurse(subclass)

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                file_path = os.path.join(root, file)
                try:
                    module = import_module(file_path)
                    for name, obj in module.__dict__.items():
                        if isinstance(obj, type) and issubclass(obj, base_class) and obj != base_class:
                            if obj not in subclasses:
                                subclasses.append(obj)
                                recurse(obj)
                except Exception as e:
                    print(f"Error importing {file_path}: {e}")

    return subclasses