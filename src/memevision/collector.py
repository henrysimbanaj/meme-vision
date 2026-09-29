"""Bucle de recolección sin ventanas: cuenta regresiva y grabación de vectores (spec 005)."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, Protocol

import numpy as np

from memevision.contracts import LandmarkResult
from memevision.dataset import SessionWriter
from memevision.features import NoPersonError, transform


class FrameSource(Protocol):
    def get_frame(self) -> np.ndarray | None: ...


class Extractor(Protocol):
    def extract(self, frame: np.ndarray) -> LandmarkResult: ...


@dataclass(frozen=True)
class CollectState:
    phase: Literal["countdown", "recording"]
    remaining_s: float
    samples: int
    person_visible: bool
    landmarks: LandmarkResult | None = None


ShowFn = Callable[[np.ndarray | None, CollectState], bool]


def run_collection(
    camera: FrameSource,
    detector: Extractor,
    writer: SessionWriter,
    countdown_s: float,
    duration_s: float,
    show: ShowFn,
    clock: Callable[[], float] = time.monotonic,
) -> int:
    """Graba un vector por cada frame con persona durante `duration_s`, tras `countdown_s`.

    Devuelve cuántas muestras guardó. Si `show` devuelve False, se cancela.
    """
    start = clock()
    while True:
        frame = camera.get_frame()
        elapsed = clock() - start
        if elapsed >= countdown_s + duration_s:
            break
        recording = elapsed >= countdown_s
        landmarks = detector.extract(frame) if frame is not None else None
        visible = landmarks is not None and landmarks.has_person
        if recording and visible:
            try:
                writer.add(transform(landmarks))
            except NoPersonError:
                visible = False
        remaining = (countdown_s if not recording else countdown_s + duration_s) - elapsed
        state = CollectState(
            phase="recording" if recording else "countdown",
            remaining_s=max(remaining, 0.0),
            samples=writer.samples,
            person_visible=visible,
            landmarks=landmarks,
        )
        if not show(frame, state):
            break
    return writer.samples
