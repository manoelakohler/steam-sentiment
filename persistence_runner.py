"""Coleta com persistência: python persistence_runner.py 620 --runs 2"""

import argparse
import json
from pathlib import Path
import sqlite3
import sys

from collection import SteamCollectionError
from workflow import collect_and_store


def main() -> int:
    parser = argparse.ArgumentParser(description="Coleta, analisa reviews novas e salva no SQLite.")
    parser.add_argument("app_id", type=int)
    parser.add_argument("--db", type=Path, default=Path("data/reviews.sqlite3"))
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--runs", type=int, default=1, help="Número de coletas consecutivas")
    args = parser.parse_args()
    if args.runs < 1:
        parser.error("--runs deve ser positivo")
    print(f"Banco: {args.db.resolve()}", flush=True)
    try:
        for run in range(1, args.runs + 1):
            result = collect_and_store(args.app_id, db_path=args.db, limit=args.limit)
            print(f"Coleta {run}: {json.dumps(result)}", flush=True)
    except (ValueError, SteamCollectionError, OSError, sqlite3.Error) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
