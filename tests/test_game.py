import random

import pytest

from memevision.contracts import NEUTRAL, UNSURE, Prediction
from memevision.game import Game, Mode, Phase

MEMES = ["michi-fuerza", "michi-silencio", "michi-67"]


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def p(meme: str, conf: float = 0.9) -> Prediction:
    return Prediction(meme, conf, {meme: conf})


def make(mode=Mode.CHALLENGE, memes=MEMES, rounds=10):
    clock = Clock()
    return Game(memes, mode=mode, rng=random.Random(1), clock=clock, rounds=rounds), clock


def advance(game, clock, seconds, visible=True, pred=None, stable=False, step=0.1):
    state = None
    for _ in range(round(seconds / step)):
        clock.t += step
        state = game.update(visible, pred, stable)
    return state


def to_analyzing(game, clock):
    advance(game, clock, 1.1)  # DETECTADA -> CUENTA
    return advance(game, clock, 3.1)  # CUENTA -> ANALIZANDO


def test_UX_01_sin_persona_busca():
    game, clock = make()
    assert advance(game, clock, 3, visible=False).phase == Phase.SEARCHING


def test_UX_02_persona_detectada_y_luego_cuenta():
    game, clock = make()
    assert advance(game, clock, 0.3).phase == Phase.DETECTED
    assert advance(game, clock, 0.9).phase == Phase.COUNTDOWN


def test_UX_03_cuenta_de_3_segundos():
    game, clock = make()
    state = advance(game, clock, 1.1)
    assert state.phase == Phase.COUNTDOWN and state.remaining_s == pytest.approx(3.0, abs=0.15)
    assert advance(game, clock, 2.8).phase == Phase.COUNTDOWN
    assert advance(game, clock, 0.3).phase == Phase.ANALYZING


def test_UX_04_analiza_3_s_aunque_la_prediccion_sea_estable():
    game, clock = make()
    to_analyzing(game, clock)
    state = advance(game, clock, 2.8, pred=p("michi-67"), stable=True)
    assert state.phase == Phase.ANALYZING
    state = advance(game, clock, 0.3, pred=p("michi-67"), stable=True)
    assert state.phase == Phase.RESULT and state.result.meme == "michi-67"


def test_UX_04_sin_ninguna_prediccion_es_no_seguro():
    game, clock = make()
    to_analyzing(game, clock)
    state = advance(game, clock, 3.1)
    assert state.phase == Phase.RESULT and state.result.meme == UNSURE


def test_UX_05_exito_solo_si_coincide_con_el_objetivo():
    game, clock = make()
    target = to_analyzing(game, clock).target
    assert target in MEMES
    state = advance(game, clock, 3.0, pred=p(target), stable=True)
    assert state.success is True

    game, clock = make()
    target = to_analyzing(game, clock).target
    other = next(m for m in MEMES if m != target)
    assert advance(game, clock, 3.0, pred=p(other), stable=True).success is False


def test_UX_05_modo_libre_sin_exito():
    game, clock = make(mode=Mode.FREE)
    state = to_analyzing(game, clock)
    assert state.target is None
    assert advance(game, clock, 3.0, pred=p("michi-67"), stable=True).success is None


def test_UX_06_resultado_dura_5_s_y_cambia_el_objetivo():
    game, clock = make()
    first = to_analyzing(game, clock).target
    advance(game, clock, 3.0, pred=p(first), stable=True)
    assert advance(game, clock, 4.8).phase == Phase.RESULT
    state = advance(game, clock, 0.3, visible=False)
    assert state.phase == Phase.SEARCHING
    assert state.round == 2 and state.target != first


def test_UX_07_persona_perdida_vuelve_a_buscar():
    game, clock = make()
    advance(game, clock, 1.5)  # en CUENTA
    assert advance(game, clock, 1.0, visible=False).phase == Phase.COUNTDOWN  # tolera 1 s
    assert advance(game, clock, 0.7, visible=False).phase == Phase.SEARCHING


def test_UX_08_cambiar_de_modo_reinicia_y_en_vivo_lleva_la_prediccion():
    game, clock = make()
    to_analyzing(game, clock)
    state = game.set_mode(Mode.LIVE)
    assert state.phase == Phase.LIVE
    state = advance(game, clock, 0.1, pred=p("michi-67"))
    assert state.phase == Phase.LIVE and state.live.meme == "michi-67"
    assert game.set_mode(Mode.FREE).phase == Phase.SEARCHING


def test_UX_09_objetivo_nunca_es_neutral():
    game, _ = make(memes=[NEUTRAL, "michi-fuerza"])
    for _ in range(10):
        assert game.next_round().target == "michi-fuerza"


def test_UX_11_puntos_segun_el_parecido_al_meme_de_la_pantalla():
    game, clock = make()
    target = to_analyzing(game, clock).target
    state = advance(
        game,
        clock,
        3.0,
        pred=Prediction("otro", 0.6, {target: 0.87, "otro": 0.13}),
        stable=True,
    )
    assert state.round_points == 87 and state.score == 87
    advance(game, clock, 5.1, visible=False)
    target2 = game.state.target
    to_analyzing(game, clock)
    state = advance(
        game,
        clock,
        3.0,
        pred=Prediction("otro", 0.6, {target2: 0.4, "otro": 0.6}),
        stable=True,
    )
    assert state.round_points == 40 and state.score == 127


def test_UX_12_al_terminar_las_rondas_pasa_al_resumen():
    game, clock = make(rounds=2)
    for _ in range(2):
        target = to_analyzing(game, clock).target
        advance(game, clock, 3.0, pred=p(target, 0.5), stable=True)
        assert game.state.phase == Phase.RESULT
        advance(game, clock, 5.1, visible=False)
    assert game.state.phase == Phase.SUMMARY
    assert game.state.score == 100
    assert game.state.round == 2


def test_UX_13_volver_a_intentar_reinicia_puntaje_y_ronda():
    game, clock = make(rounds=1)
    target = to_analyzing(game, clock).target
    advance(game, clock, 3.0, pred=p(target), stable=True)
    advance(game, clock, 5.1, visible=False)
    assert game.state.phase == Phase.SUMMARY
    state = game.play_again()
    assert state.phase == Phase.SEARCHING
    assert state.round == 1 and state.score == 0 and state.round_points == 0


def test_estado_informa_si_hay_persona_visible():
    game, clock = make(mode=Mode.LIVE)
    assert advance(game, clock, 0.1, visible=True).person_visible is True
    assert advance(game, clock, 0.1, visible=False).person_visible is False
