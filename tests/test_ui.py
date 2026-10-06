import numpy as np
import pytest
from factories import full_person

from memevision.catalog import load_catalog
from memevision.contracts import NEUTRAL, UNSURE, Prediction
from memevision.game import GameState, Mode, Phase
from memevision.ui import HEIGHT, START_BUTTON, WIDTH, button_at, render, render_start

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


def test_UX_15_pantalla_de_inicio_es_1280x720_y_el_boton_jugar_responde():
    canvas = render_start()
    assert canvas.shape == (HEIGHT, WIDTH, 3)
    assert canvas.dtype == np.uint8
    x0, y0, w, h = START_BUTTON
    assert button_at(x0 + w // 2, y0 + h // 2) == "start"
    assert button_at(0, 0) is None
    assert not np.array_equal(canvas, np.full_like(canvas, canvas[0, 0]))
