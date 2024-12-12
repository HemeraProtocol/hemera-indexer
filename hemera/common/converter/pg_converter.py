from hemera.common.models import HemeraModel
from hemera.common.utils.module_loading import import_string, scan_subclass_by_path_patterns


def scan_convert_config():
    class_mapping = HemeraModel.get_all_subclasses_with_type()

    config_mapping = {}
    for _, module in class_mapping.items():
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
