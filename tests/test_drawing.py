import numpy as np
from factories import full_person

from memevision.drawing import draw_landmarks, fit_image, put_text


def test_put_text_con_tildes_dibuja_y_no_falla_en_los_bordes():
    img = np.zeros((100, 300, 3), dtype=np.uint8)
    put_text(img, "¡Imítalo! Ññ áéíóú", (10, 10), size=24)
    assert img.any()
    put_text(img, "fuera del cuadro", (500, 500))  # no lanza
    put_text(img, "centrado", (150, 50), center=True)


def test_draw_landmarks_dibuja_esqueleto_y_acepta_none():
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    draw_landmarks(img, None)
    assert not img.any()
    draw_landmarks(img, full_person())
    assert img.any()


def test_fit_image_mantiene_proporcion():
    src = np.full((100, 200, 3), 255, dtype=np.uint8)
    out = fit_image(src, 100, 100)
    assert out.shape == (100, 100, 3)
    assert out[0, 50].sum() == 0 and out[50, 50].sum() == 255 * 3  # franjas negras arriba
