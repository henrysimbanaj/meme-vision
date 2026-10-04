import numpy as np
from factories import person

from memevision.collector import run_collection
from memevision.contracts import LandmarkResult
from memevision.dataset import SessionWriter

FRAME = np.zeros((4, 4, 3), dtype=np.uint8)


class FakeCamera:
    def get_frame(self):
        return FRAME


class FakeDetector:
    """Devuelve persona o nadie según `visible(i)` para la llamada i."""

    def __init__(self, visible=lambda i: True):
        self.visible = visible
        self.calls = 0

    def extract(self, frame):
        i, self.calls = self.calls, self.calls + 1
        return person() if self.visible(i) else LandmarkResult()


class StepClock:
    """Avanza `step` segundos en cada lectura."""

    def __init__(self, step: float = 0.1):
        self.t, self.step = -step, step

    def __call__(self) -> float:
        self.t += self.step
        return self.t


def _run(tmp_path, detector=None, show=None, countdown=1.0, duration=1.0):
    states = []

    def record(frame, state):
        states.append(state)
        return True if show is None else show(frame, state)

    writer = SessionWriter("michi-fuerza", "P01", tmp_path)
    n = run_collection(
        FakeCamera(), detector or FakeDetector(), writer, countdown, duration, record, StepClock()
    )
    return n, writer, states


def test_DAT_07_cuenta_regresiva_no_guarda_y_luego_graba(tmp_path):
    n, writer, states = _run(tmp_path)
    countdown = [s for s in states if s.phase == "countdown"]
    recording = [s for s in states if s.phase == "recording"]
    assert countdown and all(s.samples == 0 for s in countdown)
    assert len(recording) == n == writer.samples
    assert 9 <= n <= 11  # 1 s grabando con pasos de 0.1 s
    assert recording[-1].remaining_s >= 0


def test_DAT_08_frames_sin_persona_no_se_guardan(tmp_path):
    n, _, states = _run(tmp_path, detector=FakeDetector(visible=lambda i: i % 2 == 0))
    recording = [s for s in states if s.phase == "recording"]
    assert n == sum(s.person_visible for s in recording)
    assert any(not s.person_visible for s in recording)


def test_DAT_09_show_false_cancela(tmp_path):
    n, _, states = _run(tmp_path, show=lambda frame, s: s.samples < 3, countdown=0.0)
    assert n == 3
