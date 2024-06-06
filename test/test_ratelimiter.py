import unittest
import os

import main


class TestRateLimiter(unittest.TestCase):
    def setUp(self):
        self.rate_limiter = main.RateLimiter(max_requests=5, period=60)

    def test_is_allowed_first_request(self):
        self.assertTrue(self.rate_limiter.is_allowed("user1"))

    def test_is_allowed_under_limit(self):
        for _ in range(5):
            self.assertTrue(self.rate_limiter.is_allowed("user1"))

    def test_is_allowed_over_limit(self):
        for _ in range(5):
            self.assertTrue(self.rate_limiter.is_allowed("user1"))
        self.assertFalse(self.rate_limiter.is_allowed("user1"))


if __name__ == '__main__':
    unittest.main()
