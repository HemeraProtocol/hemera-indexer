import ast
import glob
import os
from datetime import timezone, datetime
from sqlalchemy import func

from common.utils.module_loading import import_string

model_path_patterns = ['common/models', 'indexer/modules/*/*/models']


def scan_convert_config():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

    mapping = {}
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
                            full_class_path = os.path.join(module_import_path[:-3], cls)
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


domain_model_mapping = scan_convert_config()
