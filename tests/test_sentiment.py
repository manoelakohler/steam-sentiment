import unittest
from unittest.mock import patch

from sentiment import analyze_reviews, _get_classifier


class SentimentTests(unittest.TestCase):
    def setUp(self):
        _get_classifier.cache_clear()
        self.reviews = [
            {"review_id": "1", "timestamp": 1700000000, "texto": "Great game!",
             "voted_up": True, "votes_up": 3, "playtime_forever": 120},
            {"review_id": "2", "timestamp": 1700000001, "texto": "Terrible game.",
             "voted_up": False, "votes_up": 1, "playtime_forever": 30},
        ]

    def tearDown(self):
        _get_classifier.cache_clear()

    def test_batch_adds_sentiment_without_changing_original_reviews(self):
        predictions = [{"label": "POSITIVE", "score": 0.99},
                       {"label": "NEGATIVE", "score": 0.95}]
        with patch("sentiment.pipeline") as factory:
            factory.return_value.return_value = predictions
            result = analyze_reviews(self.reviews, batch_size=2)
        self.assertEqual(result[0], {**self.reviews[0], "label": "POSITIVE", "confidence": 0.99})
        self.assertEqual(result[1], {**self.reviews[1], "label": "NEGATIVE", "confidence": 0.95})
        self.assertNotIn("label", self.reviews[0])
        factory.return_value.assert_called_once_with(
            ["Great game!", "Terrible game."], batch_size=2, truncation=True, max_length=512
        )

    def test_model_is_reused_across_calls(self):
        with patch("sentiment.pipeline") as factory:
            factory.return_value.return_value = [{"label": "POSITIVE", "score": 0.9}]
            analyze_reviews(self.reviews[:1])
            analyze_reviews(self.reviews[:1])
        self.assertEqual(factory.call_count, 1)

    def test_empty_input_does_not_load_model(self):
        with patch("sentiment.pipeline") as factory:
            self.assertEqual(analyze_reviews([]), [])
            factory.assert_not_called()

    def test_invalid_batch_size_and_blank_text_are_rejected(self):
        for batch_size in [0, -1, True, 1.5]:
            with self.subTest(batch_size=batch_size), self.assertRaises(ValueError):
                analyze_reviews(self.reviews, batch_size=batch_size)
        with self.assertRaises(ValueError):
            analyze_reviews([{**self.reviews[0], "texto": "   "}])


if __name__ == "__main__":
    unittest.main()
