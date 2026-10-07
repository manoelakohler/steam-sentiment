"""Runner manual: python manual_runner.py 620"""

import argparse
import json
import sys

from collection import SteamCollectionError, fetch_reviews


def main() -> int:
    parser = argparse.ArgumentParser(description="Busca reviews recentes da Steam.")
    parser.add_argument("app_id", type=int, help="App ID do jogo, por exemplo 620")
    parser.add_argument("--limit", type=int, default=100, help="Quantidade de reviews (1 a 100)")
    parser.add_argument("--timeout", type=float, default=10.0, help="Timeout em segundos")
    args = parser.parse_args()

    try:
        reviews = fetch_reviews(args.app_id, limit=args.limit, timeout=args.timeout)
    except (ValueError, SteamCollectionError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    print(f"App ID {args.app_id}: {len(reviews)} reviews recebidas.")
    print("Amostra das primeiras 5 reviews (texto limitado a 160 caracteres):")
    for review in reviews[:5]:
        preview = dict(review)
        preview["texto"] = " ".join(review["texto"].split())[:160]
        print(json.dumps(preview, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
