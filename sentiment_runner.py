"""Teste manual com reviews reais: python sentiment_runner.py 620 --limit 5"""

import argparse
import json
import sys

from collection import SteamCollectionError, fetch_reviews
from sentiment import MODEL_ID, analyze_reviews


def main() -> int:
    parser = argparse.ArgumentParser(description="Coleta e analisa reviews em inglês da Steam.")
    parser.add_argument("app_id", type=int)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()
    try:
        reviews = fetch_reviews(args.app_id, limit=args.limit)
        analyzed = analyze_reviews(reviews, batch_size=args.batch_size)
    except (ValueError, SteamCollectionError, OSError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    print(f"Modelo: {MODEL_ID}")
    print(f"App ID {args.app_id}: {len(analyzed)} reviews analisadas.")
    for review in analyzed:
        print(json.dumps({
            "review_id": review["review_id"],
            "texto": " ".join(review["texto"].split())[:160],
            "label": review["label"],
            "confidence": round(review["confidence"], 4),
            "voted_up": review["voted_up"],
            "matches_voted_up": (review["label"] == "POSITIVE") == review["voted_up"],
        }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
