"""Coleta de reviews pela API pública da Steam, sem dependências externas."""

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen
from typing import TypedDict


class Review(TypedDict):
    review_id: str
    timestamp: int
    texto: str
    voted_up: bool
    votes_up: int
    playtime_forever: int


class SteamCollectionError(RuntimeError):
    """Erro de comunicação com a Steam ou resposta inválida da API."""


def fetch_reviews(
    app_id: int | str, *, limit: int = 100, timeout: float = 10.0
) -> list[Review]:
    """Busca uma página de reviews recentes somente em inglês.

    timestamp é o Unix timestamp de criação (segundos).
    playtime_forever é o tempo total de jogo em minutos.
    A API pode retornar menos reviews que o limite solicitado.
    """
    app_id_text = str(app_id)
    if not app_id_text.isascii() or not app_id_text.isdecimal() or int(app_id_text) <= 0:
        raise ValueError("App ID deve ser um inteiro positivo.")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("limit deve ser um inteiro entre 1 e 100.")
    if timeout <= 0:
        raise ValueError("timeout deve ser positivo.")

    query = urlencode({
        "json": 1,
        "filter": "recent",
        "language": "english",
        "review_type": "all",
        "purchase_type": "all",
        "num_per_page": limit,
        "cursor": "*",
    })
    url = f"https://store.steampowered.com/appreviews/{int(app_id_text)}?{query}"
    try:
        with urlopen(url, timeout=timeout) as response:
            payload = json.load(response)
    except HTTPError as exc:
        raise SteamCollectionError(f"Steam retornou HTTP {exc.code}.") from exc
    except TimeoutError as exc:
        raise SteamCollectionError("Tempo limite excedido ao consultar a Steam.") from exc
    except URLError as exc:
        if isinstance(exc.reason, TimeoutError):
            raise SteamCollectionError("Tempo limite excedido ao consultar a Steam.") from exc
        raise SteamCollectionError(f"Falha de conexão com a Steam: {exc.reason}.") from exc
    except (ValueError, UnicodeError) as exc:
        raise SteamCollectionError("Steam retornou JSON inválido.") from exc

    if not isinstance(payload, dict) or payload.get("success") != 1:
        raise SteamCollectionError("A API da Steam não confirmou sucesso.")
    if not isinstance(payload.get("reviews"), list):
        raise SteamCollectionError("Resposta da Steam sem lista de reviews válida.")

    try:
        return [
            Review(
                review_id=raw["recommendationid"],
                timestamp=raw["timestamp_created"],
                texto=raw["review"],
                voted_up=raw["voted_up"],
                votes_up=raw["votes_up"],
                playtime_forever=raw["author"]["playtime_forever"],
            )
            for raw in payload["reviews"][:limit]
        ]
    except (KeyError, TypeError) as exc:
        raise SteamCollectionError("Review da Steam com campos ausentes ou inválidos.") from exc
