import threading
from urllib.parse import urlparse

from redis_dict import RedisDict


class ThreadSafeMemoryDict:
    def __init__(self):
        self._dict = {}
        self._lock = threading.Lock()

    def __getitem__(self, key):
        with self._lock:
            return self._dict[key]

    def __setitem__(self, key, value):
        with self._lock:
            self._dict[key] = value

    def __delitem__(self, key):
        with self._lock:
            del self._dict[key]

    def get(self, key, default=None):
        with self._lock:
            return self._dict.get(key, default)


class CacheDict:
    def __init__(self, uri=None):
        if not uri:
            self._dict = ThreadSafeMemoryDict()
        else:
            if uri.startswith('redis://'):
                redis_config = self._parse_redis_uri(uri)
                self._dict = RedisDict(**redis_config)
            else:
                raise ValueError('Unsupported URI scheme')

    def _parse_redis_uri(self, uri):
        parsed = urlparse(uri)
        redis_config = {
            'host': parsed.hostname or '127.0.0.1',
            'port': parsed.port or 6379,
        }
        if parsed.username:
            redis_config['username'] = parsed.username
        if parsed.password:
            redis_config['password'] = parsed.password
        if parsed.path and parsed.path != '/':
            redis_config['db'] = int(parsed.path.strip('/'))
        return redis_config

    def __getitem__(self, key):
        return self._dict[key]

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __delitem__(self, key):
        del self._dict[key]

    def get(self, key, default=None):
        return self._dict.get(key, default)