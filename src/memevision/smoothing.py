"""Suavizado temporal de predicciones: promedio, umbral y estabilidad (spec 008)."""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable

from memevision.contracts import UNSURE, Prediction

WINDOW = 15
THRESHOLD = 0.65
HOLD_S = 0.7


class Smoother:
    def __init__(
        self,
        window: int = WINDOW,
        threshold: float = THRESHOLD,
        hold_s: float = HOLD_S,
        clock: Callable[[], float] = time.monotonic,
    ):
        if window < 1:
            raise ValueError("window debe ser >= 1")
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold debe estar en [0, 1]")
        self.threshold, self.hold_s = threshold, hold_s
        self._clock = clock
        self._buffer: deque[dict[str, float]] = deque(maxlen=window)
        self._current: str | None = None
        self._since = 0.0
        self._now = 0.0

    def update(self, prediction: Prediction | None) -> Prediction | None:
        self._now = self._clock()
        if prediction is None:
            self.reset()
            return None
        self._buffer.append(dict(prediction.probabilities) or {prediction.meme: 1.0})
        classes = sorted({c for probs in self._buffer for c in probs})
        n = len(self._buffer)
        avg = {c: sum(p.get(c, 0.0) for p in self._buffer) / n for c in classes}
        best = max(avg, key=avg.get)
        confidence = min(avg[best], 1.0)
        meme = best if confidence >= self.threshold else UNSURE

        if meme != self._current:
            self._current, self._since = meme, self._now
        return Prediction(meme, confidence, avg)

    @property
    def stable_for_s(self) -> float:
        if self._current in (None, UNSURE):
            return 0.0
        return self._now - self._since

    @property
    def stable(self) -> bool:
        return self._current not in (None, UNSURE) and self.stable_for_s >= self.hold_s

    def reset(self) -> None:
        self._buffer.clear()
        self._current = None
        self._since = self._now
