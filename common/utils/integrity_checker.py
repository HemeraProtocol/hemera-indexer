#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Time    : 2024/10/22 上午11:53
Author  : xuzh
Project : hemera_indexer
"""

import hashlib
from pathlib import Path
from typing import Dict, List, Set, Union


class CodeIntegrityChecker:
    def __init__(self):
        self.code_hashes: Dict[str, str] = {}
        self._cached_files: Set[str] = set()

    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate the SHA256 hash of the source code"""
        try:
            with open(file_path, "rb") as f:
                self.code_hashes[file_path] = hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            print(f"Error calculating hash for file {file_path}: {e}")
            return None

    def calculate_combined_hash(self) -> str:
        """Calculate the combined hash value of all file hashes"""

        items = sorted(self.code_hashes.items())
        if not items:
            return hashlib.sha256(b"").hexdigest()

        while len(items) > 1:
            new_items = []
            for i in range(0, len(items), 2):
                if i + 1 < len(items):
                    combined = f"{items[i][0]}:{items[i][1]}+{items[i + 1][0]}:{items[i + 1][1]}"
                else:
                    combined = f"{items[i][0]}:{items[i][1]}"
                new_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
                new_items.append((f"level_{i // 2}", new_hash))
            items = new_items

        return items[0][1]

    def scan_directories(self, dir_paths: Union[List[str], str]):
        if isinstance(dir_paths, str):
            self.scan_directory(dir_paths)
        elif isinstance(dir_paths, list):
            for dir_path in dir_paths:
                self.scan_directory(dir_path)
        else:
            raise TypeError(f"dir_paths must be a string or a list of strings")

    def scan_directory(self, directory: str, exclude_patterns: Set[str] = None):
        """Gets the hash value of the specified directory"""
        if exclude_patterns is None:
            exclude_patterns = {".git", "__pycache__", "*.pyc", "*.pyo", "*.pyd", ".venv", ".env"}

        directory_path = Path(directory).resolve()

        def should_exclude(path: Path) -> bool:
            for pattern in exclude_patterns:
                if path.match(pattern) or any(parent.match(pattern) for parent in path.parents):
                    return True
            return False

        try:
            for file_path in directory_path.rglob("*.py"):
                if should_exclude(file_path):
                    continue

                self.calculate_file_hash(str(file_path))

        except Exception as e:
            print(f"Error scanning directory {directory}: {e}")

    def get_code_hashes(self) -> Dict[str, str]:
        return self.code_hashes

    def get_combined_hash(self) -> str:
        return self.calculate_combined_hash()


if __name__ == "__main__":
    checker = CodeIntegrityChecker()
    checker.scan_directories(["../../common", "../../indexer"])
    code_hashes = checker.get_code_hashes()

    for key in code_hashes.keys():
        print(f"{key}: {code_hashes[key]}")
    # print({
    #     "version": "1.0",
    #     "code_hashes": checker.get_code_hashes(),
    #     "combined_hash": checker.get_combined_hash()
    # })
