import unittest

from dashboard_data import sentiment_chart_data, select_review_examples


class DashboardDataTests(unittest.TestCase):
    def test_daily_rates_and_distribution_use_saved_review_creation_dates(self):
        reviews = [
            {"timestamp": 1704153600, "label": "POSITIVE"},
            {"timestamp": 1704067200, "label": "POSITIVE"},
            {"timestamp": 1704070800, "label": "NEGATIVE"},
        ]
        distribution, daily = sentiment_chart_data(reviews)
        self.assertEqual(distribution, {"Positivo": 2, "Negativo": 1})
        self.assertEqual(daily, [
            {"date": "2024-01-01", "positive_percentage": 50.0, "total": 2},
            {"date": "2024-01-02", "positive_percentage": 100.0, "total": 1},
        ])

    def test_does_not_fill_days_without_reviews(self):
        distribution, daily = sentiment_chart_data([
            {"timestamp": 1704067200, "label": "NEGATIVE"},
            {"timestamp": 1704240000, "label": "NEGATIVE"},
        ])
        self.assertEqual(distribution, {"Positivo": 0, "Negativo": 2})
        self.assertEqual([row["date"] for row in daily], ["2024-01-01", "2024-01-03"])
        self.assertEqual([row["positive_percentage"] for row in daily], [0.0, 0.0])

    def test_empty_input_has_no_temporal_points(self):
        self.assertEqual(sentiment_chart_data([]), ({"Positivo": 0, "Negativo": 0}, []))


class ReviewExampleTests(unittest.TestCase):
    def test_sections_filter_sort_and_limit_independently(self):
        reviews = [
            {"review_id": "p-low", "texto": "Fine", "label": "POSITIVE", "confidence": 0.6, "voted_up": True},
            {"review_id": "n-high", "texto": "Bad", "label": "NEGATIVE", "confidence": 0.99, "voted_up": True},
            {"review_id": "p-high", "texto": "Great", "label": "POSITIVE", "confidence": 0.98, "voted_up": False},
            {"review_id": "n-mid", "texto": "Poor", "label": "NEGATIVE", "confidence": 0.9, "voted_up": False},
            {"review_id": "p-mid", "texto": "Good", "label": "POSITIVE", "confidence": 0.85, "voted_up": True},
        ]
        result = select_review_examples(reviews, limit=2)
        self.assertEqual([review["review_id"] for review in result["positive"]], ["p-high", "p-mid"])
        self.assertEqual([review["review_id"] for review in result["negative"]], ["n-high", "n-mid"])
        self.assertEqual([review["review_id"] for review in result["disagreements"]], ["n-high", "p-high"])
        self.assertEqual(reviews[0]["review_id"], "p-low")

    def test_default_limit_is_five(self):
        reviews = [{"review_id": str(i), "texto": "Good", "label": "POSITIVE",
                    "confidence": i / 10, "voted_up": False} for i in range(10)]
        result = select_review_examples(reviews)
        self.assertEqual(len(result["positive"]), 5)
        self.assertEqual(len(result["disagreements"]), 5)
        self.assertEqual(result["negative"], [])
        self.assertEqual(result["positive"][0]["review_id"], "9")

    def test_empty_reviews_return_empty_sections(self):
        self.assertEqual(select_review_examples([]), {"positive": [], "negative": [], "disagreements": []})


if __name__ == "__main__":
    unittest.main()
