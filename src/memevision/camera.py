"""Fuente de frames uniforme: webcam, archivo de video o carpeta de imágenes (spec 001)."""

from __future__ import annotations

import logging
import sys
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import cv2
import numpy as np

log = logging.getLogger(__name__)

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
REOPEN_INTERVAL_S = 1.0

CaptureFactory = Callable[[int | str], Any]  # devuelve algo con la API de cv2.VideoCapture


class Camera:
    """Entrega frames BGR `uint8` de forma `(H, W, 3)`, o `None` si no hay frame.

    - `source` int: webcam. Si se desconecta, reintenta abrirla como máximo 1 vez por segundo.
    - `source` carpeta: sus imágenes en orden alfabético; luego `None`.
    - `source` archivo: un video; al terminar, `None`.
    """

    def __init__(
        self,
        source: int | str | Path = 0,
        mirror: bool = True,
        capture_factory: CaptureFactory = cv2.VideoCapture,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.mirror = mirror
        self._factory = capture_factory
        self._clock = clock
        self._released = False
        self._capture: Any = None
        self._images: Iterator[Path] | None = None
        self._is_webcam = isinstance(source, int)

        if self._is_webcam:
            self._source: int | str = source
            self._open_capture()
            return

        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"La fuente {path} no existe")
        if path.is_dir():
            files = sorted(p for p in path.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
            self._images = iter(files)
        else:
            self._source = str(path)
            self._open_capture()

    def get_frame(self) -> np.ndarray | None:
        if self._released:
            return None
        frame = self._read_image() if self._images is not None else self._read_capture()
        if frame is not None and self.mirror:
            frame = cv2.flip(frame, 1)
        return frame

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        self._released = True

    def __enter__(self) -> Camera:
        return self

    def __exit__(self, *exc: object) -> None:
        self.release()

    def _read_image(self) -> np.ndarray | None:
        for path in self._images:
            frame = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if frame is not None:
                return frame
            log.warning("No se pudo leer la imagen %s; se omite", path)
        return None

    def _read_capture(self) -> np.ndarray | None:
        frame = self._try_read()
        can_reopen = self._is_webcam and self._clock() - self._last_open >= REOPEN_INTERVAL_S
        if frame is None and can_reopen:
            log.warning("La cámara %s no entrega frames; se intenta reabrir", self._source)
            self._open_capture()
            frame = self._try_read()
        return frame

    def _try_read(self) -> np.ndarray | None:
        if self._capture is None or not self._capture.isOpened():
            return None
        ok, frame = self._capture.read()
        return frame if ok else None

    def _open_capture(self) -> None:
        if self._capture is not None:
            self._capture.release()
        self._last_open = self._clock()
        self._capture = self._factory(self._source)
        if not self._capture.isOpened():
            hint = _permission_hint()
            log.error("No se pudo abrir la cámara o el video %s.%s", self._source, hint)


def _permission_hint() -> str:
    if sys.platform == "darwin":
        return (
            " En macOS, da permiso de cámara a la Terminal o al IDE: "
            "Ajustes → Privacidad y seguridad → Cámara."
        )
    return " Revisa que la cámara esté conectada y que ningún otro programa la esté usando."
