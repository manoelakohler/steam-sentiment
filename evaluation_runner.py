"""Avalia previsões salvas, sem baixar o modelo ou consultar a Steam."""

import argparse
import json
from pathlib import Path
import sys

from evaluation import evaluate_reviews


def main() -> int:
    parser = argparse.ArgumentParser(description="Compara sentimento com voted_up.")
    parser.add_argument("sample", nargs="?", type=Path,
                        default=Path(__file__).parent / "samples" / "previous_sentiment_sample.json")
    args = parser.parse_args()
    try:
        reviews = json.loads(args.sample.read_text(encoding="utf-8"))
        if not isinstance(reviews, list):
            raise ValueError("O arquivo deve conter uma lista de reviews analisadas.")
        result = evaluate_reviews(reviews)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    print(f"Amostra: {args.sample.name} ({result['total']} reviews)")
    print("Classe positiva: POSITIVE / voted_up=True")
    for metric in ("accuracy", "precision", "recall", "f1"):
        print(f"{metric}: {result[metric]:.4f}")
    print("Matriz de confusão: linhas reais / colunas previstas; NEGATIVE, POSITIVE")
    print("[[TN, FP], [FN, TP]] =", result["confusion_matrix"])
    print(f"Discordâncias: {len(result['disagreements'])}")
    print(json.dumps(result["disagreements"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
