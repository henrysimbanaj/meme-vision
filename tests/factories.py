"""LandmarkResult sintéticos para tests, sin cámara ni MediaPipe."""

from __future__ import annotations

import numpy as np
import pandas as pd

from memevision.contracts import LandmarkResult
from memevision.features import FEATURE_NAMES

# Índices de MediaPipe Pose
NOSE, L_EYE, R_EYE, L_EAR, R_EAR = 0, 2, 5, 7, 8
MOUTH_L, MOUTH_R = 9, 10
L_SHOULDER, R_SHOULDER, L_ELBOW, R_ELBOW, L_WRIST, R_WRIST = 11, 12, 13, 14, 15, 16

# Persona parada con los brazos abajo, en coordenadas normalizadas de imagen (y hacia abajo).
NEUTRAL_POSE = {
    NOSE: (0.50, 0.30),
    L_EYE: (0.52, 0.28),
    R_EYE: (0.48, 0.28),
    L_EAR: (0.55, 0.29),
    R_EAR: (0.45, 0.29),
    MOUTH_L: (0.51, 0.34),
    MOUTH_R: (0.49, 0.34),
    L_SHOULDER: (0.60, 0.50),
    R_SHOULDER: (0.40, 0.50),
    L_ELBOW: (0.63, 0.65),
    R_ELBOW: (0.37, 0.65),
    L_WRIST: (0.64, 0.80),
    R_WRIST: (0.36, 0.80),
}


def pose(**overrides: tuple[float, float]) -> np.ndarray:
    """Pose (33, 3). `overrides` usa los nombres de este módulo en minúsculas: l_wrist=(x, y)."""
    arr = np.zeros((33, 3))
    arr[:, :2] = (0.5, 0.6)
    for idx, xy in NEUTRAL_POSE.items():
        arr[idx, :2] = xy
    names = {k.lower(): v for k, v in globals().items() if isinstance(v, int) and k.isupper()}
    for name, xy in overrides.items():
        arr[names[name], :2] = xy
    return arr


def hand(wrist: tuple[float, float], extended: tuple[bool, ...] = (True,) * 5, size=0.08):
    """Mano (21, 3) con la palma hacia la cámara y los dedos hacia arriba.

    `extended` = (pulgar, índice, medio, anular, meñique). Un dedo doblado deja su punta
    cerca de la base del dedo.
    """
    wx, wy = wrist
    arr = np.zeros((21, 3))
    arr[0] = (wx, wy, 0)
    bases_x = (-0.5, -0.25, 0.0, 0.25, 0.5)  # separación de los dedos, en unidades de `size`
    for finger, (bx, ext) in enumerate(zip(bases_x, extended, strict=True)):
        mcp = 1 + finger * 4
        for joint in range(4):
            if finger == 0:  # pulgar hacia el costado
                x = wx + size * (bx - 0.25 * joint * (1.0 if ext else 0.2))
                y = wy - size * (0.3 + 0.2 * joint * (1.0 if ext else 0.2))
            else:
                reach = 0.35 * joint if ext else 0.05 * joint
                x = wx + size * bx
                y = wy - size * (1.0 + reach)
            arr[mcp + joint] = (x, y, -0.02 * joint)
    return arr


def face(mouth: tuple[float, float] = (0.50, 0.34)) -> np.ndarray:
    arr = np.zeros((478, 3))
    arr[:, :2] = (0.50, 0.28)
    arr[13, :2] = (mouth[0], mouth[1] - 0.005)  # labio superior
    arr[14, :2] = (mouth[0], mouth[1] + 0.005)  # labio inferior
    return arr


def person(
    pose_arr: np.ndarray | None = None,
    left_hand: np.ndarray | None = None,
    right_hand: np.ndarray | None = None,
    face_arr: np.ndarray | None = None,
    blendshapes: dict[str, float] | None = None,
) -> LandmarkResult:
    return LandmarkResult(
        pose=pose() if pose_arr is None else pose_arr,
        left_hand=left_hand,
        right_hand=right_hand,
        face=face_arr,
        face_blendshapes=blendshapes,
    )


def full_person() -> LandmarkResult:
    return person(
        left_hand=hand((0.64, 0.80)),
        right_hand=hand((0.36, 0.80), extended=(False, True, False, False, False)),
        face_arr=face(),
        blendshapes={"jawOpen": 0.2, "mouthSmileLeft": 0.6, "eyeBlinkLeft": 0.1},
    )


def transformed(lm: LandmarkResult, fn) -> LandmarkResult:
    """Aplica `fn` (sobre arrays (N, 3)) a todas las partes presentes."""

    def apply(a):
        return None if a is None else fn(np.asarray(a, dtype=np.float64))

    return LandmarkResult(
        pose=apply(lm.pose),
        left_hand=apply(lm.left_hand),
        right_hand=apply(lm.right_hand),
        face=apply(lm.face),
        face_blendshapes=lm.face_blendshapes,
    )


LABELS = ("michi-fuerza", "michi-silencio", "neutral")


def synthetic(persons=("P01", "P02", "P03"), per_class=40, seed=0) -> pd.DataFrame:
    """Cada clase es una nube de puntos alrededor de un centro distinto."""
    rng = np.random.default_rng(seed)
    rows = []
    for person in persons:
        offset = rng.normal(0, 0.1, len(FEATURE_NAMES))  # cada persona es un poco distinta
        for k, label in enumerate(LABELS):
            center = np.zeros(len(FEATURE_NAMES))
            center[k * 5 : k * 5 + 5] = 3.0
            X = center + offset + rng.normal(0, 0.3, (per_class, len(FEATURE_NAMES)))
            for x in X:
                rows.append(
                    {
                        "label": label,
                        "person": person,
                        "session": "s",
                        "feature_version": "1.0",
                        **dict(zip(FEATURE_NAMES, x, strict=True)),
                    }
                )
    return pd.DataFrame(rows)
