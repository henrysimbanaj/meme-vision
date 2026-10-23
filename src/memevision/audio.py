"""Reproducción de música MP3 con salida de audio multiplataforma."""

from __future__ import annotations

import threading
from pathlib import Path

import miniaudio
import numpy as np
import sounddevice as sd

from memevision.config import ROOT

AUDIO_DIR = ROOT / "assets" / "audio"
BACKGROUND_MUSIC = AUDIO_DIR / "musictheme.mp3"
CELEBRATION_MUSIC = AUDIO_DIR / "fnafcelebracion.mp3"


class AudioPlayer:
    """Decodifica MP3 y los reproduce en un hilo sin bloquear la interfaz."""

    def __init__(self, output=sd):
        self._output = output
        self._thread: threading.Thread | None = None
        self._error: Exception | None = None
        self._stop_event = threading.Event()
        self._finished = True
        self._loop = False
        self._samples: np.ndarray | None = None
        self._sample_rate = 0

    def play(self, path: Path, *, loop: bool = False) -> None:
        self.stop()
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"No se encontró la pista de audio: {path}")
        decoded = miniaudio.decode_file(
            str(path), output_format=miniaudio.SampleFormat.FLOAT32, nchannels=2
        )
        self._samples = np.frombuffer(decoded.samples, dtype=np.float32).reshape(-1, 2)
        self._sample_rate = decoded.sample_rate
        self._loop = loop
        self._finished = False
        self._error = None
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._play_loop, daemon=True)
        self._thread.start()

    def _play_loop(self) -> None:
        try:
            while not self._stop_event.is_set():
                self._output.play(self._samples, self._sample_rate, blocking=True)
                if not self._loop:
                    break
        except Exception as exc:
            self._error = exc
        finally:
            self._finished = True

    def stop(self) -> None:
        thread = self._thread
        if thread is None:
            return
        self._stop_event.set()
        self._output.stop()
        thread.join(timeout=2)
        self._thread = None
        self._samples = None
        self._finished = True

    @property
    def finished(self) -> bool:
        return self._finished

    @property
    def error(self) -> Exception | None:
        return self._error

    @property
    def is_playing(self) -> bool:
        return self._thread is not None and self._thread.is_alive() and not self._finished

    def close(self) -> None:
        self.stop()

    def __enter__(self) -> AudioPlayer:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
