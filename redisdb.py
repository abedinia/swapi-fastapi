import os
import json
import redis
import sys


class RedisJsonConnection:
    def __init__(self):
        self.host = os.getenv("REDIS_HOST")
        self.port = os.getenv("REDIS_PORT")
        self.db = os.getenv("REDIS_DB")
        self.ttl = int(os.getenv("REDIS_TTL", 60))
        self.connection = None
        self.get_connection()

    def get_connection(self):
        try:
            if self.connection is None:
                pool = redis.ConnectionPool(host=self.host, port=self.port, db=self.db)
                self.connection = redis.Redis(connection_pool=pool)
                self.connection.ping()
            return True
        except redis.ConnectionError as e:
            print(f"Failed to connect to Redis: {e}", file=sys.stderr)
            return False

    def close_connection(self):
        if self.connection:
            self.connection.close()

    def add_to_cache(self, key, value):
        try:
            self.connection.setex(key, self.ttl, json.dumps(value))
        except redis.RedisError as e:
            print(f"Failed to add to cache: {e}", file=sys.stderr)
            sys.exit(1)

    def get_from_cache(self, key):
        try:
            cached_value = self.connection.get(key)
            if cached_value:
                try:
                    return json.loads(cached_value)
                except json.JSONDecodeError:
                    return None
        except redis.RedisError as e:
            print(f"Failed to get from cache: {e}", file=sys.stderr)
            sys.exit(1)
