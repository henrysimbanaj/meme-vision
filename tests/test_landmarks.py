import time
from dataclasses import dataclass, field

import numpy as np
import pytest

from memevision.config import MODELS_DIR
from memevision.landmarks import MODEL_URLS, LandmarkDetector


@dataclass
class P:
    """Punto como los NormalizedLandmark de MediaPipe."""

    x: float
    y: float
    z: float = 0.0


@dataclass
class Cat:
    """Categoría como los blendshapes de MediaPipe."""

    category_name: str
    score: float


@dataclass
class Raw:
    pose_landmarks: list = field(default_factory=list)
    left_hand_landmarks: list = field(default_factory=list)
    right_hand_landmarks: list = field(default_factory=list)
    face_landmarks: list = field(default_factory=list)
    face_blendshapes: list | None = None


def _points(n: int, x: float = 0.25) -> list[P]:
    return [P(x, i / n, 0.1) for i in range(n)]


def _full_raw() -> Raw:
    return Raw(
        pose_landmarks=_points(33),
        left_hand_landmarks=_points(21, x=0.1),
        right_hand_landmarks=_points(21, x=0.9),
        face_landmarks=_points(478),
        face_blendshapes=[Cat("_neutral", 0.3), Cat("jawOpen", 0.7), Cat("eyeBlinkLeft", 0.1)],
    )


class FakeBackend:
    def __init__(self, raw: Raw):
        self.raw = raw
        self.calls: list[tuple[np.ndarray, int]] = []

    def __call__(self, rgb: np.ndarray, timestamp_ms: int) -> Raw:
        self.calls.append((rgb, timestamp_ms))
        return self.raw


FRAME = np.zeros((48, 64, 3), dtype=np.uint8)


def test_LMK_01_sin_persona_todo_es_none():
    det = LandmarkDetector(backend=FakeBackend(Raw()))
    result = det.extract(FRAME)
    assert result.has_person is False
    assert result.pose is None and result.left_hand is None and result.right_hand is None
    assert result.face is None and result.face_blendshapes is None


def test_LMK_02_formas_y_blendshapes():
    det = LandmarkDetector(mirrored=False, backend=FakeBackend(_full_raw()))
    result = det.extract(FRAME)
    assert result.has_person
    assert result.pose.shape == (33, 3)
    assert result.left_hand.shape == (21, 3)
    assert result.right_hand.shape == (21, 3)
    assert result.face.shape == (478, 3)
    assert result.face_blendshapes == {"jawOpen": pytest.approx(0.7), "eyeBlinkLeft": 0.1}
    assert all(0.0 <= v <= 1.0 for v in result.face_blendshapes.values())


def test_LMK_03_sin_espejo_las_coordenadas_no_cambian():
    backend = FakeBackend(_full_raw())
    result = LandmarkDetector(mirrored=False, backend=backend).extract(FRAME)
    assert result.left_hand[0, 0] == pytest.approx(0.1)
    assert result.right_hand[0, 0] == pytest.approx(0.9)


def test_LMK_03_con_espejo_el_detector_ve_la_vista_real_y_x_se_invierte():
    frame = np.zeros((2, 4, 3), dtype=np.uint8)
    frame[:, 0] = (255, 0, 0)  # BGR azul en la columna izquierda del frame espejado
    backend = FakeBackend(_full_raw())

    result = LandmarkDetector(mirrored=True, backend=backend).extract(frame)

    rgb_sent = backend.calls[0][0]
    np.testing.assert_array_equal(rgb_sent[:, -1], np.array([[0, 0, 255]] * 2))  # desespejado y RGB
    # la mano izquierda de la persona sigue siendo left_hand; su x pasa al sistema espejado
    assert result.left_hand[0, 0] == pytest.approx(0.9)
    assert result.right_hand[0, 0] == pytest.approx(0.1)
    assert result.pose[0, 1] == pytest.approx(0.0)  # y no cambia


def test_LMK_04_sin_modelo_error_con_instrucciones(tmp_path):
    with pytest.raises(FileNotFoundError, match="download_models.py"):
        LandmarkDetector(models_dir=tmp_path)


def test_LMK_04_hay_url_oficial_para_cada_modelo():
    assert MODEL_URLS
    assert all(
        url.startswith("https://storage.googleapis.com/mediapipe-models/")
        for url in MODEL_URLS.values()
    )


def test_LMK_06_timestamps_automaticos_estrictamente_crecientes():
    backend = FakeBackend(Raw())
    det = LandmarkDetector(backend=backend)
    for _ in range(5):
        det.extract(FRAME)
    stamps = [ts for _, ts in backend.calls]
    assert all(b > a for a, b in zip(stamps, stamps[1:], strict=False))


def test_LMK_06_timestamp_explicito_se_respeta():
    backend = FakeBackend(Raw())
    LandmarkDetector(backend=backend).extract(FRAME, timestamp_ms=1234)
    assert backend.calls[0][1] == 1234


@pytest.mark.slow
@pytest.mark.skipif(
    not all((MODELS_DIR / n).exists() for n in MODEL_URLS),
    reason="falta el modelo: python scripts/download_models.py",
)
def test_LMK_05_modelo_real_frame_negro_y_velocidad():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    with LandmarkDetector() as det:
        assert det.extract(frame).has_person is False
        start = time.perf_counter()
        for _ in range(30):
            det.extract(frame)
        avg_ms = (time.perf_counter() - start) / 30 * 1000
    assert avg_ms < 80, f"extract tarda {avg_ms:.1f} ms"
