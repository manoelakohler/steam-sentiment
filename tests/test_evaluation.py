import unittest

from evaluation import evaluate_reviews


class EvaluationTests(unittest.TestCase):
    def review(self, review_id, voted_up, label):
        return {"review_id": review_id, "texto": "Example", "voted_up": voted_up,
                "label": label, "confidence": 0.9}

    def test_metrics_confusion_matrix_and_disagreements(self):
        reviews = [self.review("tp1", True, "POSITIVE"),
                   self.review("tp2", True, "POSITIVE"),
                   self.review("tn", False, "NEGATIVE"),
                   self.review("fp", False, "POSITIVE"),
                   self.review("fn", True, "NEGATIVE")]
        result = evaluate_reviews(reviews)
        self.assertEqual(result["total"], 5)
        self.assertAlmostEqual(result["accuracy"], 0.6)
        self.assertAlmostEqual(result["precision"], 2 / 3)
        self.assertAlmostEqual(result["recall"], 2 / 3)
        self.assertAlmostEqual(result["f1"], 2 / 3)
        self.assertEqual(result["confusion_matrix"], [[1, 1], [1, 2]])
        self.assertEqual(result["disagreements"], reviews[3:])

    def test_precision_and_recall_use_different_denominators(self):
        reviews = [self.review("tp", True, "POSITIVE"),
                   self.review("fp1", False, "POSITIVE"),
                   self.review("fp2", False, "POSITIVE")]
        result = evaluate_reviews(reviews)
        self.assertAlmostEqual(result["precision"], 1 / 3)
        self.assertEqual(result["recall"], 1.0)
        self.assertAlmostEqual(result["f1"], 0.5)

    def test_zero_denominators_return_zero(self):
        result = evaluate_reviews([self.review("tn", False, "NEGATIVE")])
        self.assertEqual(result["accuracy"], 1.0)
        self.assertEqual(result["precision"], 0.0)
        self.assertEqual(result["recall"], 0.0)
        self.assertEqual(result["f1"], 0.0)

    def test_empty_sample_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_reviews([])

    def test_invalid_label_or_vote_is_rejected(self):
        for review in [self.review("1", True, "NEUTRAL"),
                       self.review("2", "false", "NEGATIVE")]:
            with self.subTest(review=review), self.assertRaises(ValueError):
                evaluate_reviews([review])


if __name__ == "__main__":
    unittest.main()
