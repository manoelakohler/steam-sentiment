import sqlite3
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from persistence import ReviewStore
from workflow import collect_and_store


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "data" / "reviews.sqlite3"
        self.review = {"review_id": "123", "timestamp": 1700000000,
                       "texto": "Great game!", "voted_up": True, "votes_up": 7,
                       "playtime_forever": 120, "label": "POSITIVE", "confidence": 0.98}

    def tearDown(self):
        self.temp.cleanup()

    def test_creates_database_and_preserves_all_fields_after_reopening(self):
        with ReviewStore(self.db) as store:
            self.assertEqual(store.save_reviews(620, [self.review]), 1)
        with ReviewStore(self.db) as store:
            self.assertEqual(store.list_reviews(620), [self.review])
            self.assertEqual(store.count_reviews(620), 1)
            self.assertEqual(store.count_reviews(730), 0)
            self.assertEqual(store.existing_ids(["123", "456"]), {"123"})

    def test_duplicate_id_is_not_inserted_or_overwritten(self):
        with ReviewStore(self.db) as store:
            store.save_reviews(620, [self.review])
            self.assertEqual(store.save_reviews(620, [{**self.review, "texto": "Changed"}]), 0)
            self.assertEqual(store.list_reviews(620), [self.review])

    def test_batch_rolls_back_if_one_record_is_invalid(self):
        with ReviewStore(self.db) as store:
            with self.assertRaises(sqlite3.IntegrityError):
                store.save_reviews(620, [self.review, {**self.review, "review_id": "456", "confidence": 2.0}])
            self.assertEqual(store.count_reviews(620), 0)

    def test_repeated_collection_analyzes_only_new_ids(self):
        raw = {key: value for key, value in self.review.items() if key not in ("label", "confidence")}
        other = {**raw, "review_id": "456"}
        def analyze(reviews, **kwargs):
            return [{**review, "label": "POSITIVE", "confidence": 0.98} for review in reviews]
        with patch("workflow.fetch_reviews", side_effect=[[raw, raw], [raw], [raw, other]]), \
             patch("workflow.analyze_reviews", side_effect=analyze) as model:
            first = collect_and_store(620, db_path=self.db)
            second = collect_and_store(620, db_path=self.db)
            third = collect_and_store(620, db_path=self.db)
        self.assertEqual((first["analyzed"], first["inserted"], first["total"]), (1, 1, 1))
        self.assertEqual((second["analyzed"], second["inserted"], second["total"]), (0, 0, 1))
        self.assertEqual((third["analyzed"], third["inserted"], third["total"]), (1, 1, 2))
        self.assertEqual(model.call_count, 2)
        self.assertEqual(model.call_args_list[1].args[0], [other])

    def test_failed_analysis_does_not_mark_reviews_as_saved(self):
        raw = {key: value for key, value in self.review.items() if key not in ("label", "confidence")}
        with patch("workflow.fetch_reviews", return_value=[raw]), \
             patch("workflow.analyze_reviews", side_effect=RuntimeError("model failed")):
            with self.assertRaises(RuntimeError):
                collect_and_store(620, db_path=self.db)
        with ReviewStore(self.db) as store:
            self.assertEqual(store.count_reviews(620), 0)


if __name__ == "__main__":
    unittest.main()
