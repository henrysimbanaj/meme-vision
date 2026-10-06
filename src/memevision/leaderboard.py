"""Puntajes locales del modo reto. El archivo no va a git: puede tener nombres."""

from __future__ import annotations

import json
from pathlib import Path

from memevision.config import LEADERBOARD_PATH

MAX_NAME = 16
MAX_ENTRIES = 50


def load_board(path: Path = LEADERBOARD_PATH) -> list[tuple[str, int]]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    board = [(str(item["name"]), int(item["score"])) for item in raw]
    return sorted(board, key=lambda item: (-item[1], item[0]))


def record(name: str, score: int, path: Path = LEADERBOARD_PATH) -> list[tuple[str, int]]:
    """Agrega un puntaje si el nombre no está vacío. Devuelve el tablero ordenado."""
    clean = " ".join(name.split())[:MAX_NAME]
    board = load_board(path)
    if not clean:
        return board
    board.append((clean, int(score)))
    board = sorted(board, key=lambda item: (-item[1], item[0]))[:MAX_ENTRIES]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([{"name": n, "score": s} for n, s in board], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return board
