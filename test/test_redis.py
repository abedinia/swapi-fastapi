import unittest
from unittest.mock import patch
import fakeredis
import json
import os

from redisdb import RedisJsonConnection


class TestRedisJsonConnection(unittest.TestCase):

    @patch('redis.Redis', fakeredis.FakeRedis)
    def setUp(self):
        os.environ['REDIS_HOST'] = 'localhost'
        os.environ['REDIS_PORT'] = '6379'
        os.environ['REDIS_DB'] = '0'
        os.environ['REDIS_TTL'] = '60'

        self.redis_conn = RedisJsonConnection()
        self.redis_conn.get_connection()

    def tearDown(self):
        self.redis_conn.close_connection()

    def test_add_to_cache(self):
        key = "people1"
        value = {"foo": "bar"}

        self.redis_conn.add_to_cache(key, value)
        cached_value = self.redis_conn.connection.get(key)

        self.assertIsNotNone(cached_value)
        self.assertEqual(json.loads(cached_value), value)

    def test_get_from_cache(self):
        key = "test_key"
        value = {"foo": "bar"}

        self.redis_conn.connection.setex(key, 60, json.dumps(value))
        retrieved_value = self.redis_conn.get_from_cache(key)

        self.assertEqual(retrieved_value, value)

    def test_get_from_cache_invalid_json(self):
        key = "test_key"
        self.redis_conn.connection.setex(key, 60, "invalid json")

        retrieved_value = self.redis_conn.get_from_cache(key)

        self.assertIsNone(retrieved_value)

    def test_cache_expiry(self):
        key = "expire_key"
        value = {"foo": "bar"}

        self.redis_conn.add_to_cache(key, value)
        self.redis_conn.connection.expire(key, 1)

        import time
        time.sleep(2)

        cached_value = self.redis_conn.get_from_cache(key)
        self.assertIsNone(cached_value)

    def test_overwrite_cache(self):
        key = "test_key"
        value1 = {"foo": "bar"}
        value2 = {"baz": "qux"}

        self.redis_conn.add_to_cache(key, value1)
        cached_value1 = self.redis_conn.get_from_cache(key)
        self.assertEqual(cached_value1, value1)

        self.redis_conn.add_to_cache(key, value2)
        cached_value2 = self.redis_conn.get_from_cache(key)
        self.assertEqual(cached_value2, value2)

    def test_get_nonexistent_key(self):
        key = "nonexistent_key"

        cached_value = self.redis_conn.get_from_cache(key)
        self.assertIsNone(cached_value)


if __name__ == '__main__':
    unittest.main()
