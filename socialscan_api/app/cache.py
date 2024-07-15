#!/usr/bin/python3
# -*- coding: utf-8 -*-

import redis
from flask_caching import Cache

from common.utils.config import get_config

app_config = get_config()
# Use cache
cache = Cache()


class RedisDb:
    def __init__(self, host, cache_type=""):
        if cache_type == "RedisClusterCache":
            self.enable_cache = True
            self.r = redis.RedisCluster(
                host=host,
                port=6379,
                ssl=True,
            )
        elif cache_type == "RedisCache":
            self.enable_cache = True
            self.r = redis.Redis(
                host=host,
                port=6379,
                ssl=True,
                decode_responses=True,  # get() 得到字符串类型的数据
            )
        else:
            self.enable_cache = False
            self.r = None

    def handle_redis_token(self, key, value=None):
        if value:  # 如果value非空，那么就设置key和value，EXPIRE_TIME为过期时间
            self.r.set(key, value, ex=3600)
        else:  # 如果value为空，那么直接通过key从redis中取值
            redis_token = self.r.get(key)
            return redis_token

    def set_init_value(self, key, value):
        self.r.set(key, value)

    def get_next_increment_value(self, key):
        return self.r.incr(key)


redis_db = RedisDb('127.0.0.1', 'local')
