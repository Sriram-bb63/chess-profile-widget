import redis
import redis.client

pool = redis.ConnectionPool(host="localhost", port=6379, db=0, max_connections=20)

redis_client = redis.Redis(connection_pool=pool, decode_responses=True)
