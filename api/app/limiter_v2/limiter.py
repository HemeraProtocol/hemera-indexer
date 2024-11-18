from datetime import datetime, timezone
from functools import wraps

from flask import jsonify, make_response, request
from flask_limiter import Limiter

from api.app import cache
from common.models import db
from common.models.limiter import ApiKey


def get_header_api_key():
    return request.headers.get("X-API-KEY", "")


limiter_v2 = Limiter(
    key_func=get_header_api_key,
    default_limits=["1800 per hour"],
    storage_uri="memory://",
)


def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = get_header_api_key()
        if not get_api_key(api_key):
            return make_response(jsonify({"error": "Invalid API key"}), 403)
        return f(*args, **kwargs)

    return decorated


def get_api_key(api_key):
    cache_key = f"ak_{api_key}"
    api_key_from_cache = cache.cache.get(cache_key)
    if api_key_from_cache:
        # if id is -1, api key not found in db
        if api_key_from_cache.id == -1:
            return None
        return api_key_from_cache

    api_key_from_db = (
        db.session.query(ApiKey)
        .filter(ApiKey.api_key == api_key, ApiKey.expires_at > datetime.now(timezone.utc))
        .first()
    )

    if api_key_from_db:
        cache.cache.set(cache_key, api_key_from_db, 600)
        return api_key_from_db

    # if api key not found in db, set it in cache to avoid future db hits
    cache.cache.set(cache_key, ApiKey(id=-1), 300)
    return None


def get_limits():
    api_key = get_header_api_key()
    api_key_model = get_api_key(api_key)

    if api_key_model:
        return api_key_model.limits

    return []
