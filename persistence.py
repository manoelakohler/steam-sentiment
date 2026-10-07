"""Persistência local de reviews analisadas usando SQLite."""

from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentiment import AnalyzedReview


class ReviewStore:
    def __init__(self, db_path: str | Path = "data/reviews.sqlite3"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(db_path))
        self.connection.row_factory = sqlite3.Row
        with self.connection:
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    review_id TEXT PRIMARY KEY NOT NULL,
                    app_id INTEGER NOT NULL,
                    timestamp INTEGER NOT NULL,
                    texto TEXT NOT NULL,
                    voted_up INTEGER NOT NULL CHECK (voted_up IN (0, 1)),
                    votes_up INTEGER NOT NULL,
                    playtime_forever INTEGER NOT NULL,
                    label TEXT NOT NULL CHECK (label IN ('POSITIVE', 'NEGATIVE')),
                    confidence REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1)
                )
            """)
            self.connection.execute("CREATE INDEX IF NOT EXISTS reviews_app_id ON reviews(app_id)")

    def __enter__(self) -> ReviewStore:
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()

    def existing_ids(self, review_ids: list[str]) -> set[str]:
        """Verifica os IDs da página coletada (no máximo 100 reviews)."""
        if not review_ids:
            return set()
        placeholders = ",".join("?" for _ in review_ids)
        rows = self.connection.execute(
            f"SELECT review_id FROM reviews WHERE review_id IN ({placeholders})", review_ids
        )
        return {row["review_id"] for row in rows}

    def save_reviews(self, app_id: int, reviews: list[AnalyzedReview]) -> int:
        """Salva o lote em uma transação; IDs existentes são preservados."""
        values = [
            (review["review_id"], app_id, review["timestamp"], review["texto"],
             review["voted_up"], review["votes_up"], review["playtime_forever"],
             review["label"], review["confidence"])
            for review in reviews
        ]
        before = self.connection.total_changes
        with self.connection:
            self.connection.executemany("""
                INSERT INTO reviews
                    (review_id, app_id, timestamp, texto, voted_up, votes_up,
                     playtime_forever, label, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(review_id) DO NOTHING
            """, values)
        return self.connection.total_changes - before

    def count_reviews(self, app_id: int) -> int:
        return self.connection.execute(
            "SELECT COUNT(*) FROM reviews WHERE app_id = ?", (app_id,)
        ).fetchone()[0]

    def list_reviews(self, app_id: int) -> list[AnalyzedReview]:
        rows = self.connection.execute("""
            SELECT review_id, timestamp, texto, voted_up, votes_up,
                   playtime_forever, label, confidence
            FROM reviews WHERE app_id = ? ORDER BY timestamp DESC, review_id
        """, (app_id,))
        result = []
        for row in rows:
            review = dict(row)
            review["voted_up"] = bool(review["voted_up"])
            result.append(review)
        return result
