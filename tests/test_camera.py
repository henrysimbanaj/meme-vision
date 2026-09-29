from pathlib import Path

import cv2
import numpy as np
import pytest

from memevision.camera import Camera


def _write_images(folder: Path, n: int) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        img = np.full((48, 64, 3), i * 40, dtype=np.uint8)
        cv2.imwrite(str(folder / f"img_{i:02d}.png"), img)


def _write_video(path: Path, n_frames: int) -> None:
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10, (64, 48))
    assert writer.isOpened(), "este OpenCV no puede escribir MJPG/.avi"
    for i in range(n_frames):
        writer.write(np.full((48, 64, 3), i * 20, dtype=np.uint8))
    writer.release()


class FakeCapture:
    """VideoCapture falso: entrega `frames` frames y después falla como una webcam desconectada."""

    def __init__(self, frames: int = 0, opened: bool = True):
        self.frames = frames
        self.opened = opened
        self.released = False

    def isOpened(self) -> bool:  # noqa: N802 (misma API que cv2.VideoCapture)
        return self.opened and not self.released

    def read(self):
        if self.released or self.frames <= 0:
            return False, None
        self.frames -= 1
        return True, np.zeros((48, 64, 3), dtype=np.uint8)

    def release(self) -> None:
        self.released = True


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_CAM_01_carpeta_con_3_imagenes_da_3_frames_y_luego_none(tmp_path):
    _write_images(tmp_path, 3)
    with Camera(tmp_path, mirror=False) as cam:
        frames = [cam.get_frame() for _ in range(4)]

    for frame in frames[:3]:
        assert isinstance(frame, np.ndarray)
        assert frame.dtype == np.uint8
        assert frame.ndim == 3 and frame.shape[2] == 3
    assert frames[3] is None


def test_CAM_01_carpeta_entrega_las_imagenes_en_orden_alfabetico(tmp_path):
    _write_images(tmp_path, 3)
    with Camera(tmp_path, mirror=False) as cam:
        values = [int(cam.get_frame()[0, 0, 0]) for _ in range(3)]
    assert values == [0, 40, 80]


def test_CAM_01_carpeta_ignora_archivos_que_no_son_imagenes(tmp_path):
    _write_images(tmp_path, 2)
    (tmp_path / "notas.txt").write_text("no soy una imagen")
    with Camera(tmp_path) as cam:
        assert cam.get_frame() is not None
        assert cam.get_frame() is not None
        assert cam.get_frame() is None


def test_CAM_02_video_leido_hasta_el_final_devuelve_none_sin_excepcion(tmp_path):
    video = tmp_path / "clip.avi"
    _write_video(video, 5)
    with Camera(video, mirror=False) as cam:
        frames = []
        while (frame := cam.get_frame()) is not None:
            frames.append(frame)
            assert len(frames) <= 5
        assert cam.get_frame() is None  # seguir pidiendo tras el final tampoco falla

    assert len(frames) == 5
    assert all(f.dtype == np.uint8 and f.shape == (48, 64, 3) for f in frames)


def test_CAM_03_mirror_voltea_horizontalmente(tmp_path):
    img = np.zeros((48, 64, 3), dtype=np.uint8)
    img[:, :32] = 255  # mitad izquierda blanca
    cv2.imwrite(str(tmp_path / "asimetrica.png"), img)

    with Camera(tmp_path, mirror=True) as cam:
        mirrored = cam.get_frame()
    with Camera(tmp_path, mirror=False) as cam:
        original = cam.get_frame()

    np.testing.assert_array_equal(original, img)
    np.testing.assert_array_equal(mirrored, img[:, ::-1])


def test_CAM_04_webcam_desconectada_devuelve_none_y_reintenta_max_1_vez_por_segundo():
    clock = FakeClock()
    captures: list[FakeCapture] = []

    def factory(source):
        # la primera captura da 1 frame y se "desconecta"; las siguientes no abren
        cap = FakeCapture(frames=1) if not captures else FakeCapture(opened=False)
        captures.append(cap)
        return cap

    cam = Camera(0, capture_factory=factory, clock=clock)
    assert cam.get_frame() is not None
    assert len(captures) == 1

    clock.now = 0.5
    assert cam.get_frame() is None  # falla, pero no ha pasado 1 s desde que se abrió
    assert len(captures) == 1

    clock.now = 1.2
    assert cam.get_frame() is None
    assert len(captures) == 2  # primer reintento
    assert captures[0].released  # la captura rota se libera antes de reabrir

    clock.now = 1.9
    assert cam.get_frame() is None
    assert len(captures) == 2  # todavía no pasó 1 s desde el reintento

    clock.now = 2.3
    assert cam.get_frame() is None
    assert len(captures) == 3
    cam.release()


def test_CAM_04_webcam_vuelve_a_dar_frames_tras_reconectar():
    clock = FakeClock()
    captures: list[FakeCapture] = []

    def factory(source):
        cap = FakeCapture(frames=0 if not captures else 2)
        captures.append(cap)
        return cap

    cam = Camera(0, capture_factory=factory, clock=clock)
    assert cam.get_frame() is None
    clock.now = 1.0
    assert cam.get_frame() is not None
    cam.release()


def test_CAM_05_salir_del_with_libera_la_captura():
    captures: list[FakeCapture] = []

    def factory(source):
        captures.append(FakeCapture(frames=10))
        return captures[-1]

    with Camera(0, capture_factory=factory) as cam:
        assert cam.get_frame() is not None
    assert captures[0].released
    assert cam.get_frame() is None  # ya liberada: no reabre ni falla


def test_CAM_05_release_es_idempotente(tmp_path):
    _write_images(tmp_path, 1)
    cam = Camera(tmp_path)
    cam.release()
    cam.release()
    assert cam.get_frame() is None


def test_borde_indice_de_camara_inexistente_devuelve_none_y_avisa(caplog):
    def factory(source):
        return FakeCapture(opened=False)

    with Camera(7, capture_factory=factory) as cam:
        assert cam.get_frame() is None
    assert "cámara" in caplog.text.lower()


def test_borde_ruta_inexistente_lanza_error_claro(tmp_path):
    with pytest.raises(FileNotFoundError, match="no existe"):
        Camera(tmp_path / "no_existe.avi")
