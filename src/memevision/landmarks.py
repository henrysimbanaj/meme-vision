"""Frame BGR -> LandmarkResult con MediaPipe HolisticLandmarker (spec 002)."""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from memevision.config import MODELS_DIR
from memevision.contracts import LandmarkResult

HOLISTIC_MODEL = "holistic_landmarker.task"
MODEL_URLS = {
    HOLISTIC_MODEL: "https://storage.googleapis.com/mediapipe-models/holistic_landmarker/"
    "holistic_landmarker/float16/latest/holistic_landmarker.task",
}

Backend = Callable[[np.ndarray, int], Any]  # (rgb, timestamp_ms) -> HolisticLandmarkerResult


class LandmarkDetector:
    """Detecta pose (33), manos (21 c/u), cara (478) y blendshapes de una persona.

    Con `mirrored=True` el frame viene espejado (vista selfie). El detector recibe la vista real
    de la cámara, así `left_hand` es siempre la mano izquierda **de la persona**; luego las x se
    pasan al sistema del frame espejado (`1 - x`) para poder dibujarlas encima.
    """

    def __init__(
        self, models_dir: Path = MODELS_DIR, mirrored: bool = True, backend: Backend | None = None
    ):
        self.mirrored = mirrored
        self._landmarker = None
        self._last_ts = -1
        self._backend = backend or self._create_mediapipe_backend(Path(models_dir))

    def extract(self, frame: np.ndarray, timestamp_ms: int | None = None) -> LandmarkResult:
        if self.mirrored:
            frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        raw = self._backend(rgb, self._next_timestamp(timestamp_ms))
        return LandmarkResult(
            pose=self._to_array(raw.pose_landmarks),
            left_hand=self._to_array(raw.left_hand_landmarks),
            right_hand=self._to_array(raw.right_hand_landmarks),
            face=self._to_array(raw.face_landmarks),
            face_blendshapes=_blendshapes(raw.face_blendshapes),
        )

    def close(self) -> None:
        if self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None

    def __enter__(self) -> LandmarkDetector:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _to_array(self, points: Sequence[Any] | None) -> np.ndarray | None:
        if not points:
            return None
        arr = np.array([(p.x, p.y, p.z) for p in points], dtype=np.float32)
        if self.mirrored:
            arr[:, 0] = 1.0 - arr[:, 0]
        return arr

    def _next_timestamp(self, timestamp_ms: int | None) -> int:
        if timestamp_ms is None:
            timestamp_ms = max(int(time.monotonic() * 1000), self._last_ts + 1)
        self._last_ts = timestamp_ms
        return timestamp_ms

    def _create_mediapipe_backend(self, models_dir: Path) -> Backend:
        model_path = models_dir / HOLISTIC_MODEL
        if not model_path.exists():
            raise FileNotFoundError(
                f"No se encontró {model_path.name} en {models_dir}: "
                "ejecuta `python scripts/download_models.py`"
            )
        import mediapipe as mp  # import tardío: los tests rápidos no cargan MediaPipe
        from mediapipe.tasks.python import BaseOptions, vision

        options = vision.HolisticLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            output_face_blendshapes=True,
        )
        self._landmarker = vision.HolisticLandmarker.create_from_options(options)

        def detect(rgb: np.ndarray, timestamp_ms: int) -> Any:
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
            return self._landmarker.detect_for_video(image, timestamp_ms)

        return detect


def _blendshapes(categories: Sequence[Any] | None) -> dict[str, float] | None:
    if not categories:
        return None
    return {
        c.category_name: float(np.clip(c.score, 0.0, 1.0))
        for c in categories
        if c.category_name != "_neutral"
    }
