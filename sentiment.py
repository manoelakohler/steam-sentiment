"""Inferência binária de sentimento para reviews em inglês."""

from functools import cache
from typing import Literal

from transformers import pipeline

from collection import Review

MODEL_ID = "distilbert/distilbert-base-uncased-finetuned-sst-2-english"


class AnalyzedReview(Review):
    label: Literal["POSITIVE", "NEGATIVE"]
    confidence: float


@cache
def _get_classifier():
    """Carrega na primeira chamada e reutiliza o modelo no processo."""
    return pipeline("sentiment-analysis", model=MODEL_ID, device=-1)


def analyze_reviews(reviews: list[Review], *, batch_size: int = 8) -> list[AnalyzedReview]:
    """Retorna cópias das reviews com label e confidence (score entre 0 e 1).

    Textos longos são truncados em 512 tokens. A confiança é o score do
    modelo para a classe escolhida, não uma garantia de acerto.
    """
    if isinstance(batch_size, bool) or not isinstance(batch_size, int) or batch_size < 1:
        raise ValueError("batch_size deve ser um inteiro positivo.")
    if not reviews:
        return []
    texts = [review["texto"] for review in reviews]
    if any(not text.strip() for text in texts):
        raise ValueError("Não é possível analisar reviews com texto vazio.")

    predictions = _get_classifier()(
        texts, batch_size=batch_size, truncation=True, max_length=512
    )
    return [
        AnalyzedReview(**review, label=prediction["label"], confidence=float(prediction["score"]))
        for review, prediction in zip(reviews, predictions, strict=True)
    ]
