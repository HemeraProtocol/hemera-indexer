from functools import wraps

feature_router = {}


class FeatureRegistry:
    def __init__(self):
        self.features = {}
        self.feature_list = []

    def register(self, feature_name, subcategory):
        def decorator(f):
            if feature_name not in self.features:
                self.features[feature_name] = {}
                self.feature_list.append(feature_name)
            self.features[feature_name][subcategory] = f

            @wraps(f)
            def wrapper(*args, **kwargs):
                return f(*args, **kwargs)

            return wrapper

        return decorator


feature_registry = FeatureRegistry()
register_feature = feature_registry.register
