# Limiter V2

## Usage

```python
from limiter_v2 import limiter_v2, require_api_key, get_limits


# require_api_key, user default limits
@explorer_namespace.route("/v1/some_resource")
class SomeResource(Resource):
    @require_api_key
    @cache.cached(timeout=300, query_string=True)
    def get(self):
        return {"message": "Hello, world!"}, 200


# require_api_key, user custom limits
@explorer_namespace.route("/v1/some_resource")
class SomeResource(Resource):
    @cache.cached(timeout=300, query_string=True)
    @limiter_v2.limit(get_limits)
    @require_api_key
    def get(self):
        return {"message": "Hello, world!"}, 200


# require_api_key, user custom limits with cost
@explorer_namespace.route("/v1/some_resource")
class SomeResource(Resource):
    @cache.cached(timeout=300, query_string=True)
    @limiter_v2.limit(get_limits, cost=2)
    @require_api_key
    def get(self):
        return {"message": "Hello, world!"}, 200

# require_api_key, user custom limits with cost, if user has no limits, use default limits
@explorer_namespace.route("/v1/some_resource")
class SomeResource(Resource):
    @cache.cached(timeout=300, query_string=True)
    @limiter_v2.limit(get_limits, cost=2, override_defaults=False)
    @require_api_key
    def get(self):
        return {"message": "Hello, world!"}, 200
```
