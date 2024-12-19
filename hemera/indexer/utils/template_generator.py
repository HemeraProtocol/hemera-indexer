#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Time    : 2024/12/3 下午5:35
Author  : xuzh
Project : hemera_indexer
"""
import copy
from pathlib import Path


class TemplateGenerator:
    def __init__(self, template_file: str = None):
        if template_file:
            with open(Path(template_file), "r", encoding="utf-8") as f:
                self.template_file = f.read()
        else:
            self.template_file = ""
        self.replacements = {}

    def add_replacements(self, key: dict, value: str):
        self.replacements[key] = value

    def generate_file(self, target_path: str) -> None:
        generate_content = copy.deepcopy(self.template_file)
        for key, value in self.replacements.items():
            generate_content = generate_content.replace(key, value)

        target_path = Path(target_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(generate_content)
