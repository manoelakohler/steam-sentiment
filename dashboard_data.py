"""Prepara dados dos gráficos sem depender da interface ou do banco."""

from datetime import datetime, timezone
from typing import Literal, TypedDict

from evaluation import EvaluationReview, evaluate_reviews


class ChartReview(TypedDict):
    timestamp: int
    label: Literal["POSITIVE", "NEGATIVE"]


class DailySentiment(TypedDict):
    date: str
    positive_percentage: float
    total: int


def sentiment_chart_data(
    reviews: list[ChartReview],
) -> tuple[dict[str, int], list[DailySentiment]]:
    """Distribuição atual e percentual positivo por dia de criação em UTC."""
    distribution = {"Positivo": 0, "Negativo": 0}
    days: dict[str, list[int]] = {}
    for review in reviews:
        positive = review["label"] == "POSITIVE"
        distribution["Positivo" if positive else "Negativo"] += 1
        day = datetime.fromtimestamp(review["timestamp"], tz=timezone.utc).date().isoformat()
        counts = days.setdefault(day, [0, 0])
        counts[0] += int(positive)
        counts[1] += 1

    daily = [
        DailySentiment(date=day, positive_percentage=100 * positive / total, total=total)
        for day, (positive, total) in sorted(days.items())
    ]
    return distribution, daily


class ReviewExamples(TypedDict):
    positive: list[EvaluationReview]
    negative: list[EvaluationReview]
    disagreements: list[EvaluationReview]


def select_review_examples(
    reviews: list[EvaluationReview], *, limit: int = 5,
) -> ReviewExamples:
    """Seleciona até cinco exemplos por seção, com maior confiança primeiro."""
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit deve ser um inteiro positivo.")
    ranked = sorted(reviews, key=lambda review: review["confidence"], reverse=True)
    disagreements = evaluate_reviews(ranked)["disagreements"] if ranked else []
    return ReviewExamples(
        positive=[review for review in ranked if review["label"] == "POSITIVE"][:limit],
        negative=[review for review in ranked if review["label"] == "NEGATIVE"][:limit],
        disagreements=disagreements[:limit],
    )
