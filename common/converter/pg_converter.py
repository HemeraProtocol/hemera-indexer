import ast
import os
from datetime import timezone, datetime
from sqlalchemy import func

from common.utils.module_loading import import_string


def scan_convert_config(model_path):
    mapping = {}

    for file in os.listdir(model_path):
        module_file_path = os.path.join(model_path, file)
        if os.path.isfile(module_file_path) and \
                file.endswith(".py") and file != "__init__.py" and file != "bridge.py":
            with open(module_file_path, "r", encoding="utf-8") as module:
                file_content = module.read()

            parsed_content = ast.parse(file_content)
            class_names = [node.name for node in ast.walk(parsed_content) if isinstance(node, ast.ClassDef)]

            for cls in class_names:
                full_class_path = os.path.join(module_file_path[:-3], cls)
                dot_path = full_class_path.replace(os.path.sep, ".")
                module = import_string(dot_path)

                module_configs = module.model_domain_mapping()
                if module_configs:
                    for config in module_configs:
                        mapping[config['domain']] = {
                            'table': module,
                            'conflict_do_update': config['conflict_do_update'],
                            'update_strategy': config['update_strategy'],
                            'converter': config['converter']
                        }

    return mapping


domain_model_mapping = scan_convert_config("common/models")
