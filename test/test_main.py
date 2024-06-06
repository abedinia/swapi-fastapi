import unittest
from unittest.mock import patch, Mock
from fastapi import HTTPException

import requests

import main


class TestCheckParams(unittest.TestCase):
    def test_valid_param_people(self):
        try:
            main.check_params("people")
        except HTTPException as e:
            self.fail(f"check_params raised HTTPException unexpectedly: {e}")

    def test_valid_param_planets(self):
        try:
            main.check_params("planets")
        except HTTPException as e:
            self.fail(f"check_params raised HTTPException unexpectedly: {e}")

    def test_valid_param_starships(self):
        try:
            main.check_params("starships")
        except HTTPException as e:
            self.fail(f"check_params raised HTTPException unexpectedly: {e}")

    def test_invalid_param(self):
        with self.assertRaises(HTTPException) as context:
            main.check_params("invalid_param")

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Invalid parameter: invalid_param")

    def test_invalid_peoples(self):
        with self.assertRaises(HTTPException) as context:
            main.check_params("peoples")

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Invalid parameter: peoples")


class TestMakeRequest(unittest.TestCase):
    @patch('requests.get')
    def test_make_request_success(self, mock_get):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"people response": "example response"}
        mock_get.return_value = mock_response

        result = main.make_request("people", "1")
        self.assertEqual(result, {"people response": "example response"})
        mock_get.assert_called_once_with(f"{main.swapi_uri}/people/1")

    @patch('requests.get')
    def test_make_request_http_error_with_json(self, mock_get):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "invalid request"}
        mock_get.return_value = mock_response

        with self.assertRaises(HTTPException) as context:
            main.make_request("people", "1")

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, {"error": "invalid request"})
        mock_get.assert_called_once_with(f"{main.swapi_uri}/people/1")

    @patch('requests.get')
    def test_make_request_http_error_without_json(self, mock_get):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_response.status_code = 500
        mock_response.json.side_effect = ValueError()
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        with self.assertRaises(HTTPException) as context:
            main.make_request("people", "1")

        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(context.exception.detail, "Internal Server Error")
        mock_get.assert_called_once_with(f"{main.swapi_uri}/people/1")

    @patch('requests.get')
    def test_make_request_request_exception(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException()

        with self.assertRaises(HTTPException) as context:
            main.make_request("people", "1")

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "Server not found")
        mock_get.assert_called_once_with(f"{main.swapi_uri}/people/1")


if __name__ == '__main__':
    unittest.main()
