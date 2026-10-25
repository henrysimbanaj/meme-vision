import numpy as np

from scripts.demo import _fit_to_viewport, _viewport_to_canvas


def test_UX_25_pantalla_completa_escala_y_centra_sin_deformar():
    canvas = np.full((720, 1280, 3), 255, dtype=np.uint8)

    fitted = _fit_to_viewport(canvas, 1920, 1200)

    assert fitted.shape == (1200, 1920, 3)
    assert np.all(fitted[:60] == 0)
    assert np.all(fitted[60:1140] == 255)
    assert np.all(fitted[1140:] == 0)


def test_UX_25_clics_se_convierten_a_coordenadas_del_lienzo():
    assert _viewport_to_canvas(960, 600, 1920, 1200) == (640, 360)
    assert _viewport_to_canvas(960, 30, 1920, 1200)[1] < 0
