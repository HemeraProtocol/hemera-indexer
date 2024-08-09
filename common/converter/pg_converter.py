from common.models import HemeraModel, model_path_patterns
from common.utils.module_loading import import_string, scan_subclass_by_path_patterns


def scan_convert_config():
    class_mapping = scan_subclass_by_path_patterns(model_path_patterns, HemeraModel)

    config_mapping = {}
    for class_name, path in class_mapping.items():
        full_class_path = path['cls_import_path']
        module = import_string(full_class_path)

        module_configs = module.model_domain_mapping()
        if module_configs:
            for config in module_configs:
                config_mapping[config["domain"]] = {
                    "table": module,
                    "conflict_do_update": config["conflict_do_update"],
                    "update_strategy": config["update_strategy"],
                    "converter": config["converter"],
                }
    return config_mapping


domain_model_mapping = scan_convert_config()
