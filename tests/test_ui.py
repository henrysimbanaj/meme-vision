import numpy as np
import pytest
from factories import full_person

from memevision.catalog import load_catalog
from memevision.contracts import NEUTRAL, UNSURE, Prediction
from memevision.game import GameState, Mode, Phase
from memevision.ui import (
    ACCENT,
    GAME_CYAN,
    GAME_MINT,
    GAME_PROMPTS,
    HEIGHT,
    START_BUTTON,
    START_LOGO_PATH,
    START_MEME_IDS,
    WHITE,
    WIDTH,
    YELLOW,
    _bars,
    _footer,
    _game_background,
    _progress_color,
    _result,
    button_at,
    feedback_for,
    render,
    render_start,
)

CATALOG = load_catalog()
MEME = next(iter(CATALOG))
FRAME = np.full((480, 640, 3), 90, dtype=np.uint8)


def pred(meme: str) -> Prediction:
    return Prediction(meme, 0.8, {meme: 0.8, NEUTRAL: 0.2})


STATES = [
    GameState(Mode.CHALLENGE, Phase.SEARCHING, 1, MEME),
    GameState(Mode.CHALLENGE, Phase.DETECTED, 1, MEME, 0.5),
    GameState(Mode.CHALLENGE, Phase.COUNTDOWN, 1, MEME, 2.4),
    GameState(Mode.CHALLENGE, Phase.ANALYZING, 1, MEME, 3.0, live=pred(MEME)),
    GameState(Mode.CHALLENGE, Phase.RESULT, 1, MEME, 4.0, result=pred(MEME), success=True),
    GameState(Mode.CHALLENGE, Phase.RESULT, 2, MEME, 4.0, result=pred(NEUTRAL), success=False),
    GameState(Mode.FREE, Phase.SEARCHING, 1, None),
    GameState(Mode.FREE, Phase.RESULT, 1, None, result=Prediction(UNSURE, 0.4)),
    GameState(Mode.LIVE, Phase.LIVE, 1, None, live=pred(MEME)),
    GameState(Mode.LIVE, Phase.LIVE, 1, None),
    GameState(Mode.CHALLENGE, Phase.SUMMARY, 10, None, score=640, total_rounds=10),
]


@pytest.mark.parametrize("state", STATES, ids=lambda s: f"{s.mode}-{s.phase}")
@pytest.mark.parametrize("with_frame", [True, False])
def test_UX_10_render_da_lienzo_1280x720_en_todas_las_fases(state, with_frame):
    frame = FRAME if with_frame else None
    lm = full_person() if with_frame else None
    canvas = render(frame, state, CATALOG, lm, banner="Aviso" if state.mode == Mode.LIVE else "")
    assert canvas.shape == (HEIGHT, WIDTH, 3)
    assert canvas.dtype == np.uint8


@pytest.mark.parametrize(
    ("points", "expected"),
    [
        (100, "Excelente"),
        (80, "Excelente"),
        (79, "Buen Trabajo"),
        (55, "Buen Trabajo"),
        (54, "Casi"),
        (30, "Casi"),
        (29, "¡Sigue intentando!"),
        (0, "¡Sigue intentando!"),
    ],
)
def test_UX_16_mensaje_de_resultado_segun_puntos(points, expected):
    assert feedback_for(points) == expected


def test_UX_22_resultado_separa_los_puntos_de_ronda_y_el_total_en_tarjetas_legibles():
    canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    state = GameState(
        Mode.CHALLENGE, Phase.RESULT, 2, MEME, result=pred(MEME), score=137, round_points=73
    )

    _result(canvas, state, CATALOG, 600)

    assert np.any(np.all(canvas == GAME_MINT, axis=2))
    assert np.any(np.all(canvas == GAME_CYAN, axis=2))
    assert not np.any(np.all(canvas == YELLOW, axis=2))


def test_UX_24_fondo_de_partida_oceanico_esta_animado():
    first = _game_background(0.0)
    later = _game_background(1.0)

    assert first.shape == (HEIGHT, WIDTH, 3)
    assert not np.array_equal(first, later)
    assert tuple(first[0, 0]) == (33, 26, 15)


def test_UX_15_pantalla_de_inicio_es_1280x720_y_el_boton_jugar_responde():
    canvas = render_start()
    assert canvas.shape == (HEIGHT, WIDTH, 3)
    assert canvas.dtype == np.uint8
    x0, y0, w, h = START_BUTTON
    assert button_at(x0 + w // 2, y0 + h // 2) == "start"
    assert button_at(0, 0) is None
    assert not np.array_equal(canvas, np.full_like(canvas, canvas[0, 0]))


def test_UX_19_menu_arcade_muestra_seis_memes_y_anima_el_titulo():
    first = render_start(CATALOG, time_s=0)
    later = render_start(CATALOG, time_s=0.6)

    assert len(START_MEME_IDS) == 6
    assert all(meme_id in CATALOG for meme_id in START_MEME_IDS)
    assert START_LOGO_PATH.is_file()
    assert first.shape == (HEIGHT, WIDTH, 3)
    assert np.count_nonzero(np.any(first[0:278, 300:950] != first[0, 0], axis=2)) > 1000
    assert not np.array_equal(first, later)


def test_UX_20_barra_objetivo_rojo_amarillo_verde_con_transicion_continua():
    red = np.array(_progress_color(0.0))
    yellow = np.array(_progress_color(0.5))
    green = np.array(_progress_color(1.0))

    assert tuple(red) == (45, 55, 235)
    assert tuple(yellow) == (0, 215, 255)
    assert tuple(green) == (70, 210, 65)
    assert np.max(np.abs(np.array(_progress_color(0.501)) - yellow)) <= 1
    assert _progress_color(-1.0) == _progress_color(0.0)
    assert _progress_color(2.0) == _progress_color(1.0)


def test_UX_20_barra_del_objetivo_se_mantiene_visible_aunque_no_sea_top():
    canvas = np.zeros((120, WIDTH, 3), dtype=np.uint8)
    target_prob = 0.12
    prediction = Prediction(
        "michi-burla",
        0.7,
        {"michi-burla": 0.7, "michi-67": 0.18, MEME: target_prob},
    )

    _bars(canvas, prediction, CATALOG, y=20, target=MEME)

    assert tuple(canvas[24, 260]) == _progress_color(target_prob)
    assert np.any(np.all(canvas[20:48, 960:1000] == _progress_color(target_prob), axis=2))
    assert not np.any(np.all(canvas[20:48, 0:250] == WHITE, axis=2))


def test_UX_20_porcentaje_objetivo_es_grande_y_no_aparece_leyenda_de_atajos():
    canvas = np.zeros((120, WIDTH, 3), dtype=np.uint8)
    target_prob = 0.73
    prediction = Prediction(MEME, target_prob, {MEME: target_prob})
    _bars(canvas, prediction, CATALOG, y=20, rows=1, target=MEME)
    percent_region = canvas[12:50, 960:1020]
    assert np.count_nonzero(np.any(percent_region != 0, axis=2)) > 250

    full_canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    _footer(full_canvas, GameState(Mode.CHALLENGE, Phase.SEARCHING, 1, MEME), CATALOG, 0)
    assert not np.any(np.all(full_canvas == (170, 170, 170), axis=2))


def test_UX_21_prompts_de_ronda_usan_texto_arcade_animado_cian_y_menta():
    assert GAME_PROMPTS[Phase.DETECTED][0] == "¿Listo?"
    assert GAME_PROMPTS[Phase.COUNTDOWN][0] == "¡Imita al gato!"
    assert all(color not in (ACCENT, YELLOW) for _text, color in GAME_PROMPTS.values())

    detected = GameState(Mode.CHALLENGE, Phase.DETECTED, 2, MEME)
    first = render(None, detected, CATALOG, time_s=0.0)
    later = render(None, detected, CATALOG, time_s=0.2)
    assert not np.array_equal(first, later)
