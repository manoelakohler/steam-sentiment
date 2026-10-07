import io
import json
import unittest
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from collection import SteamCollectionError, fetch_reviews


class CollectionTests(unittest.TestCase):
    def response(self, payload):
        return io.BytesIO(json.dumps(payload).encode("utf-8"))

    def test_recent_request_and_field_mapping(self):
        payload = {"success": 1, "reviews": [{
            "recommendationid": "123", "timestamp_created": 1700000000,
            "review": "Very good!", "voted_up": True, "votes_up": 7,
            "author": {"playtime_forever": 120},
        }]}
        with patch("collection.urlopen", return_value=self.response(payload)) as request:
            reviews = fetch_reviews(620)
        self.assertEqual(reviews, [{
            "review_id": "123", "timestamp": 1700000000,
            "texto": "Very good!", "voted_up": True,
            "votes_up": 7, "playtime_forever": 120,
        }])
        url = urlparse(request.call_args.args[0])
        self.assertEqual(url.scheme, "https")
        self.assertEqual(url.netloc, "store.steampowered.com")
        self.assertEqual(url.path, "/appreviews/620")
        query = parse_qs(url.query)
        self.assertEqual(query["filter"], ["recent"])
        self.assertEqual(query["num_per_page"], ["100"])
        self.assertEqual(query["language"], ["english"])
        self.assertEqual(query["purchase_type"], ["all"])
        self.assertEqual(query["json"], ["1"])
        self.assertEqual(query["cursor"], ["*"])
        self.assertEqual(request.call_args.kwargs["timeout"], 10.0)

    def test_empty_reviews_are_valid(self):
        with patch("collection.urlopen", return_value=self.response({"success": 1, "reviews": []})):
            self.assertEqual(fetch_reviews(620), [])

    def test_limit_and_timeout_can_be_selected(self):
        with patch("collection.urlopen", return_value=self.response({"success": 1, "reviews": []})) as request:
            fetch_reviews("620", limit=5, timeout=2.0)
        query = parse_qs(urlparse(request.call_args.args[0]).query)
        self.assertEqual(query["num_per_page"], ["5"])
        self.assertEqual(request.call_args.kwargs["timeout"], 2.0)

    def test_invalid_arguments_are_rejected(self):
        for kwargs in [{"app_id": 0}, {"app_id": "abc"}, {"app_id": True},
                       {"app_id": 1.5}, {"app_id": 620, "limit": 101},
                       {"app_id": 620, "limit": 0}, {"app_id": 620, "timeout": 0}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                fetch_reviews(**kwargs)

    def test_http_error_is_explained(self):
        error = HTTPError("https://store.steampowered.com", 503, "Unavailable", {}, None)
        with patch("collection.urlopen", side_effect=error):
            with self.assertRaisesRegex(SteamCollectionError, "HTTP 503"):
                fetch_reviews(620)

    def test_timeout_is_explained(self):
        for error in [TimeoutError(), URLError(TimeoutError())]:
            with self.subTest(error=error), patch("collection.urlopen", side_effect=error):
                with self.assertRaisesRegex(SteamCollectionError, "[Tt]empo|timeout"):
                    fetch_reviews(620)

    def test_connection_error_is_explained(self):
        with patch("collection.urlopen", side_effect=URLError("connection refused")):
            with self.assertRaises(SteamCollectionError):
                fetch_reviews(620)

    def test_failed_or_malformed_response_is_rejected(self):
        for payload in [{"success": 0}, {"success": 1},
                        {"success": 1, "reviews": [{}]}, []]:
            with self.subTest(payload=payload), patch("collection.urlopen", return_value=self.response(payload)):
                with self.assertRaises(SteamCollectionError):
                    fetch_reviews(620)
        with patch("collection.urlopen", return_value=io.BytesIO(b"invalid JSON")):
            with self.assertRaises(SteamCollectionError):
                fetch_reviews(620)


if __name__ == "__main__":
    unittest.main()
