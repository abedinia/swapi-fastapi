import os
import unittest
from unittest.mock import patch, Mock
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient

from dotenv import load_dotenv
load_dotenv('.env_test')

import main

client = TestClient(main.app)

class RedisJsonConnectionMock:
    def __init__(self):
        self.cache = {}

    def get_connection(self):
        return True

    def get_from_cache(self, key):
        return self.cache.get(key, None)

    def add_to_cache(self, key, value):
        self.cache[key] = value

    def close_connection(self):
        pass


class TestHandleGetRequest(unittest.TestCase):
    @patch('main.redisdb.RedisJsonConnection', new=RedisJsonConnectionMock)
    @patch('main.make_request')
    def test_handle_get_request_success(self, mock_make_request):
        mock_make_request.return_value = {"key": "value"}
        response = client.get("/people/1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"key": "value"})

    @patch('main.redisdb.RedisJsonConnection', new=RedisJsonConnectionMock)
    @patch('main.make_request')
    def test_handle_get_request_cache_hit(self, mock_make_request):
        redis_conn = RedisJsonConnectionMock()
        redis_conn.add_to_cache("people1", {"key": "cached_value"})

        with patch('main.redisdb.RedisJsonConnection', return_value=redis_conn):
            response = client.get("/people/1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"key": "cached_value"})
        mock_make_request.assert_not_called()

    @patch('main.redisdb.RedisJsonConnection', new=RedisJsonConnectionMock)
    @patch('main.make_request')
    def test_handle_get_request_rate_limit_exceeded(self, mock_make_request):
        mock_make_request.side_effect = HTTPException(status_code=429)
        response = client.get("/people/1")
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json(), {"detail": "Rate limit exceeded"})

    @patch('main.redisdb.RedisJsonConnection')
    def test_handle_get_request_server_error(self, mock_redis_conn):
        mock_redis_conn.return_value.get_connection.return_value = False
        response = client.get("/people/1")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "Error in Server Side"})


class TestHandleBatchRequest(unittest.TestCase):
    @patch('main.redisdb.RedisJsonConnection', new=RedisJsonConnectionMock)
    @patch('main.make_request')
    def test_handle_batch_request_success(self, mock_make_request):
        mock_make_request.return_value = {"key": "value"}
        batch_request = {"endpoints": ["people/1", "planets/2"]}
        response = client.post("/", json=batch_request)
        expected_response = [
            {"endpoint": "people/1", "response": {"key": "value"}},
            {"endpoint": "planets/2", "response": {"key": "value"}}
        ]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_response)

    @patch('main.redisdb.RedisJsonConnection', new=RedisJsonConnectionMock)
    @patch('main.make_request')
    def test_handle_batch_request_cache_hit(self, mock_make_request):
        redis_conn = RedisJsonConnectionMock()
        redis_conn.add_to_cache("people1", {"key": "cached_value"})
        batch_request = {"endpoints": ["people/1"]}

        with patch('main.redisdb.RedisJsonConnection', return_value=redis_conn):
            response = client.post("/", json=batch_request)

        expected_response = [{"endpoint": "people/1", "response": {"key": "cached_value"}}]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_response)
        mock_make_request.assert_not_called()

    @patch('main.redisdb.RedisJsonConnection', new=RedisJsonConnectionMock)
    def test_handle_batch_request_invalid_format(self):
        batch_request = {"endpoints": ["invalid_format"]}
        response = client.post("/", json=batch_request)
        expected_response = [{"endpoint": "invalid_format", "error": "Invalid endpoint format"}]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_response)

    @patch('main.redisdb.RedisJsonConnection')
    def test_handle_batch_request_server_error(self, mock_redis_conn):
        mock_redis_conn.return_value.get_connection.return_value = False
        batch_request = {"endpoints": ["people/1"]}
        response = client.post("/", json=batch_request)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "Error in Server Side"})

    @patch('main.redisdb.RedisJsonConnection', new=RedisJsonConnectionMock)
    @patch('main.make_request')
    def test_handle_batch_request_http_error(self, mock_make_request):
        mock_make_request.side_effect = HTTPException(status_code=400, detail="Bad request")
        batch_request = {"endpoints": ["people/1"]}
        response = client.post("/", json=batch_request)
        expected_response = [{"endpoint": "people/1", "error": "Bad request"}]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_response)
