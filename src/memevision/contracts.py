"""Tipos compartidos entre módulos (ver specs/). Cambiarlos requiere actualizar la spec y un ADR."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

NEUTRAL = "neutral"
UNSURE = "no_seguro"


@dataclass(frozen=True)
class LandmarkResult:
    """Salida de landmarks.extract(). Las partes no detectadas son None.

    Coordenadas normalizadas de MediaPipe: x, y en [0, 1] respecto a la imagen; z relativa.
    """

    pose: np.ndarray | None = None  # (33, 3)
    left_hand: np.ndarray | None = None  # (21, 3), mano izquierda de la persona
    right_hand: np.ndarray | None = None  # (21, 3)
    face: np.ndarray | None = None  # (478, 3)
    face_blendshapes: dict[str, float] | None = None  # 52 claves, valores en [0, 1]

    @property
    def has_person(self) -> bool:
        return self.pose is not None


@dataclass(frozen=True)
class Prediction:
    """Salida de classifier.predict() y de smoothing.update()."""

    meme: str
    confidence: float
    probabilities: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence fuera de [0, 1]: {self.confidence}")

    def top(self, k: int = 3) -> list[tuple[str, float]]:
        return sorted(self.probabilities.items(), key=lambda kv: kv[1], reverse=True)[:k]


@dataclass(frozen=True)
class MemeSpec:
    """Un meme del catálogo (memes/catalog/<id>/meme.yaml)."""

    id: str
    name: str
    image_path: str
    caption: str = ""
    traits: tuple[str, ...] = ()
