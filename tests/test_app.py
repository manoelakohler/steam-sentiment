import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from persistence import ReviewStore

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "reviews.sqlite3"
        self.env = patch.dict(os.environ, {"STEAM_SENTIMENT_DB": str(self.db)})
        self.env.start()
        self.reviews = [
            {"review_id": "1", "timestamp": 1700000000, "texto": "Great game!",
             "voted_up": True, "votes_up": 3, "playtime_forever": 120,
             "label": "POSITIVE", "confidence": 0.99},
            {"review_id": "2", "timestamp": 1700000001, "texto": "Not fun.",
             "voted_up": True, "votes_up": 0, "playtime_forever": 30,
             "label": "NEGATIVE", "confidence": 0.95},
        ]

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def app(self):
        return AppTest.from_file(str(APP_PATH), default_timeout=30).run()

    def test_stored_metrics_and_switching_game(self):
        with ReviewStore(self.db) as store:
            store.save_reviews(620, self.reviews)
        app = self.app()
        self.assertFalse(app.exception)
        self.assertEqual(app.title[0].value, "Steam Sentiment Monitor")
        self.assertEqual([metric.value for metric in app.metric], ["2", "—", "50.0%", "100.0%", "50.0%"])
        app.text_input[0].set_value("730").run()
        self.assertFalse(app.exception)
        self.assertEqual([metric.value for metric in app.metric], ["0", "—", "—", "—", "—"])

    def test_button_updates_database_and_preserves_latest_count(self):
        app = self.app()
        with patch("workflow.fetch_reviews", return_value=[{k: v for k, v in review.items() if k not in ("label", "confidence")} for review in self.reviews]), \
             patch("workflow.analyze_reviews", return_value=self.reviews) as analyze:
            app.button[0].click().run()
            self.assertFalse(app.exception)
            self.assertEqual([metric.value for metric in app.metric][:2], ["2", "2"])
            app.run()
            self.assertEqual(app.metric[1].value, "2")
            app.button[0].click().run()
            self.assertEqual([metric.value for metric in app.metric][:2], ["2", "0"])
            self.assertEqual(analyze.call_count, 1)

    def test_update_failure_keeps_existing_data_visible(self):
        with ReviewStore(self.db) as store:
            store.save_reviews(620, self.reviews)
        app = self.app()
        with patch("workflow.fetch_reviews", side_effect=OSError("connection unavailable")):
            app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertTrue(app.error)
        self.assertEqual(app.metric[0].value, "2")

    def test_charts_and_confusion_table_preserve_existing_metrics(self):
        with ReviewStore(self.db) as store:
            store.save_reviews(620, self.reviews)
        app = self.app()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.get("vega_lite_chart")), 2)
        self.assertEqual(app.table[0].value.to_dict("list"), {
            "Usuário na Steam": ["Não recomendou", "Recomendou"],
            "IA: negativo": [0, 1], "IA: positivo": [0, 1],
        })
        self.assertEqual([metric.value for metric in app.metric], ["2", "—", "50.0%", "100.0%", "50.0%"])
        app.text_input[0].set_value("730").run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.get("vega_lite_chart")), 0)
        self.assertEqual(len(app.table), 0)

    def test_review_sections_show_text_confidence_and_recommendation(self):
        with ReviewStore(self.db) as store:
            store.save_reviews(620, self.reviews)
        app = self.app()
        self.assertFalse(app.exception)
        self.assertEqual([header.value for header in app.subheader][-3:], [
            "Reviews positivas com maior confiança do modelo",
            "Reviews negativas com maior confiança do modelo",
            "Onde a IA discordou do usuário",
        ])
        self.assertEqual(len(app.expander), 3)
        self.assertEqual([text.value for text in app.text], ["Great game!", "Not fun.", "Not fun."])
        captions = [caption.value for caption in app.caption]
        self.assertTrue(any("99.0%" in caption and "Recomendou" in caption for caption in captions))
        self.assertTrue(any("95.0%" in caption and "Negativo" in caption for caption in captions))
        self.assertEqual(len(app.get("vega_lite_chart")), 2)
        self.assertEqual(len(app.table), 1)

    def test_invalid_app_id_does_not_collect(self):
        app = self.app()
        with patch("workflow.fetch_reviews") as fetch:
            app.text_input[0].set_value("abc").run()
            self.assertTrue(app.error)
            self.assertTrue(app.button[0].disabled)
            fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
