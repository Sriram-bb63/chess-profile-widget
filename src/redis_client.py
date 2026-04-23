import os

import redis

pool = redis.ConnectionPool(
    host="redis",
    port=6379,
    db=0,
    max_connections=20,
)

redis_client = redis.Redis(connection_pool=pool, decode_responses=True)
