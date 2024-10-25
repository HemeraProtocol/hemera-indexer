#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Time    : 2024/10/22 上午11:53
Author  : xuzh
Project : hemera_indexer
"""

import hashlib
import importlib
import inspect
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Union


class StaticCodeSignature:
    def __init__(self):
        self.exclude_patterns = {".git", "__pycache__", "*.pyc", "*.pyo", "*.pyd", ".venv", ".env", "tests"}
        self._cached_files: Set[str] = set()
        self._code_hashes: Dict[str, str] = {}
        self._combined_hash = None

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate the SHA256 hash of the source code"""
        try:
            with open(file_path, "rb") as f:
                self._code_hashes[file_path] = hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            print(f"Error calculating hash for file {file_path}: {e}")
            return None

    def _calculate_combined_hash(self):
        self._combined_hash = calculate_combined_hash(self._code_hashes)

    def calculate_signature(self, dir_paths: Union[List[str], str]):
        if isinstance(dir_paths, str):
            self._scan_directory(dir_paths)
        elif isinstance(dir_paths, list):
            for dir_path in dir_paths:
                self._scan_directory(dir_path)
        else:
            raise TypeError(f"dir_paths must be a string or a list of strings")

        self._calculate_combined_hash()

    def _scan_directory(self, directory: str):
        """Gets the hash value of the specified directory"""
        directory_path = Path(directory).resolve()

        def should_exclude(path: Path) -> bool:
            for pattern in self.exclude_patterns:
                if path.match(pattern) or any(parent.match(pattern) for parent in path.parents):
                    return True
            return False

        try:
            for file_path in directory_path.rglob("*.py"):
                if should_exclude(file_path):
                    continue

                self._calculate_file_hash(str(file_path))

        except Exception as e:
            print(f"Error scanning directory {directory}: {e}")

    def get_code_hashes(self) -> Dict[str, str]:
        return self._code_hashes

    def get_combined_hash(self) -> str:
        return self._combined_hash


class RuntimeCodeSignature:
    """
    The RuntimeCodeSignature ensures that only the actual executed code participates in the code hash calculation.
    """

    def __init__(self):
        self._project_package = ["api", "indexer", "common"]
        self._exclude_package = []
        self._processed_modules = set()
        self._module_hashes = {}
        self._combined_hash = None

    def _calculate_source_hash(self, obj) -> Optional[str]:
        """Get the source code and calculate the SHA256 hash of the source code"""
        try:
            source_code = self._get_source(obj)
            self._module_hashes[obj.__name__] = self._hash_code(source_code)
        except Exception as e:
            print(f"Error calculating hash for module {obj.__name__}: {e}")
            return None

    def _get_source(self, obj) -> Optional[str]:
        """Get the source code of an object"""
        try:
            return inspect.getsource(obj)
        except (TypeError, OSError, IOError):
            return None

    def _hash_code(self, code: str) -> str:
        """Calculate the SHA256 hash of the source code"""
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    def _should_process_module(self, module_name: str) -> bool:
        """Determines whether the module should be processed"""
        return any(module_name.startswith(package) for package in self._project_package) and not any(
            module_name.startswith(package) for package in self._exclude_package
        )

    def _recursive_find_imports(self, module) -> Set[str]:
        """Find all imports in a module"""
        imports = set()
        source = self._get_source(module)

        if not source:
            return imports

        for name, obj in inspect.getmembers(module):
            if inspect.ismodule(obj) and self._should_process_module(obj.__class__.__module__):
                imports.add(obj.__class__.__module__)
            elif hasattr(obj, "__module__") and obj.__module__ and self._should_process_module(obj.__module__):
                imports.add(obj.__module__)

        return imports

    def _process_module(self, module_name: str):
        """Processing a single module, storing its hash value"""
        if module_name in self._processed_modules:
            return

        try:
            module = sys.modules.get(module_name) or importlib.import_module(module_name)
        except Exception as e:
            raise ValueError(f"Error in calculate module {module_name} code hash: {e}")

        self._processed_modules.add(module_name)

        source = self._get_source(module)
        if not source:
            return

        self._calculate_source_hash(module)

        imports = self._recursive_find_imports(module)
        for import_name in imports:
            if import_name not in self._processed_modules:
                self._process_module(import_name)

    def calculate_signature(self, root_module_name: str = None, exclude_package: List[str] = []) -> Dict[str, str]:
        """calculate runtime code signature"""
        if root_module_name is None:
            raise ValueError("root_module_name cannot be None")

        if root_module_name not in sys.modules:
            raise ValueError(f"{root_module_name} cannot be found in imported list.")

        self._exclude_package = exclude_package
        self._process_module(root_module_name)
        self._exclude_package.clear()

    def calculate_combined_hash(self):
        self._combined_hash = calculate_combined_hash(self._module_hashes)

    def get_combined_hash(self) -> str:
        return self._combined_hash


def calculate_combined_hash(hashes: dict):
    """Calculate the combined hash value of all file hashes"""

    items = [value for key, value in sorted(hashes.items())]
    if not items:
        return hashlib.sha256(b"").hexdigest()

    while len(items) > 1:
        new_items = []
        for i in range(0, len(items), 2):
            if i + 1 < len(items):
                combined = f"{items[i]}:{items[i + 1]}"
            else:
                combined = items[i]
            new_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
            new_items.append(new_hash)
        items = new_items

    return items[0]


if __name__ == "__main__":
    checker = StaticCodeSignature()
    checker.calculate_signature(["../../common", "../../indexer"])
    code_hashes = checker.get_code_hashes()
    combined_hash = checker.get_combined_hash()

    for key in code_hashes.keys():
        print(f"{key}: {code_hashes[key]}")
    print(combined_hash)
    # print({
    #     "version": "1.0",
    #     "code_hashes": checker.get_code_hashes(),
    #     "combined_hash": checker.get_combined_hash()
    # })
