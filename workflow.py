"""Coordena coleta, análise das reviews novas e persistência."""

from pathlib import Path
from typing import TypedDict

from collection import fetch_reviews
from persistence import ReviewStore
from sentiment import analyze_reviews


class CollectionResult(TypedDict):
    collected: int
    new: int
    analyzed: int
    inserted: int
    total: int


def collect_and_store(
    app_id: int | str, *, db_path: str | Path = "data/reviews.sqlite3",
    limit: int = 100, timeout: float = 10.0, batch_size: int = 8,
) -> CollectionResult:
    """Busca uma página e analisa apenas IDs ainda não salvos.

    Reviews existentes mantêm os dados e a previsão originais.
    Uma falha de inferência não registra as reviews como processadas.
    """
    reviews = fetch_reviews(app_id, limit=limit, timeout=timeout)
    unique_reviews = {review["review_id"]: review for review in reviews}
    with ReviewStore(db_path) as store:
        existing = store.existing_ids(list(unique_reviews))
        new_reviews = [review for review_id, review in unique_reviews.items() if review_id not in existing]
        analyzed = analyze_reviews(new_reviews, batch_size=batch_size) if new_reviews else []
        inserted = store.save_reviews(int(app_id), analyzed)
        return CollectionResult(
            collected=len(reviews), new=len(new_reviews), analyzed=len(analyzed),
            inserted=inserted, total=store.count_reviews(int(app_id)),
        )
