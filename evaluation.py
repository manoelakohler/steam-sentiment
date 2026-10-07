"""Avalia sentimento previsto usando voted_up como referência."""

from typing import Literal, TypedDict


class EvaluationReview(TypedDict):
    review_id: str
    texto: str
    voted_up: bool
    label: Literal["POSITIVE", "NEGATIVE"]
    confidence: float


class EvaluationResult(TypedDict):
    total: int
    accuracy: float
    precision: float
    recall: float
    f1: float
    confusion_matrix: list[list[int]]
    disagreements: list[EvaluationReview]


def evaluate_reviews(reviews: list[EvaluationReview]) -> EvaluationResult:
    """Calcula métricas binárias; POSITIVE corresponde a voted_up=True.

    Matriz: linhas reais e colunas previstas, ambas NEGATIVE, POSITIVE.
    Formato: [[TN, FP], [FN, TP]]. Divisões por zero retornam 0.0;
    uma amostra vazia gera ValueError. Reviews discordantes mantêm seus campos.
    """
    if not reviews:
        raise ValueError("A avaliação precisa de pelo menos uma review.")

    matrix = [[0, 0], [0, 0]]
    disagreements = []
    for review in reviews:
        if review["label"] not in ("POSITIVE", "NEGATIVE"):
            raise ValueError("label deve ser POSITIVE ou NEGATIVE.")
        if not isinstance(review["voted_up"], bool):
            raise ValueError("voted_up deve ser booleano.")
        actual = int(review["voted_up"])
        predicted = int(review["label"] == "POSITIVE")
        matrix[actual][predicted] += 1
        if actual != predicted:
            disagreements.append(dict(review))

    tn, fp = matrix[0]
    fn, tp = matrix[1]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
    return EvaluationResult(
        total=len(reviews),
        accuracy=(tp + tn) / len(reviews),
        precision=precision,
        recall=recall,
        f1=f1,
        confusion_matrix=matrix,
        disagreements=disagreements,
    )
