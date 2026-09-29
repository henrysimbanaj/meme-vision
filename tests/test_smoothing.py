import pytest

from memevision.contracts import UNSURE, Prediction
from memevision.smoothing import Smoother


def pred(**probs: float) -> Prediction:
    probs = {k.replace("_", "-"): v for k, v in probs.items()}
    best = max(probs, key=probs.get)
    return Prediction(best, probs[best], probs)


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def test_SMO_01_promedia_la_ventana_y_olvida_lo_viejo():
    s = Smoother(window=2, threshold=0.0)
    s.update(pred(a=1.0, b=0.0))
    out = s.update(pred(a=0.0, b=1.0))
    assert out.probabilities == pytest.approx({"a": 0.5, "b": 0.5})
    out = s.update(pred(a=0.0, b=1.0))  # la primera ya salió del buffer
    assert out.meme == "b" and out.confidence == pytest.approx(1.0)


def test_SMO_02_baja_confianza_es_no_seguro():
    s = Smoother(window=3, threshold=0.65)
    out = s.update(pred(a=0.6, b=0.4))
    assert out.meme == UNSURE
    assert out.confidence == pytest.approx(0.6)
    assert out.probabilities == pytest.approx({"a": 0.6, "b": 0.4})


def test_SMO_03_estable_tras_hold_y_reinicia_al_cambiar():
    clock = Clock()
    s = Smoother(window=1, threshold=0.5, hold_s=0.7, clock=clock)
    s.update(pred(a=0.9, b=0.1))
    clock.t = 0.5
    s.update(pred(a=0.9, b=0.1))
    assert not s.stable and s.stable_for_s == pytest.approx(0.5)
    clock.t = 0.8
    s.update(pred(a=0.9, b=0.1))
    assert s.stable
    clock.t = 0.9
    s.update(pred(a=0.1, b=0.9))
    assert not s.stable and s.stable_for_s == 0.0


def test_SMO_04_none_reinicia():
    clock = Clock()
    s = Smoother(window=5, threshold=0.5, hold_s=0.0, clock=clock)
    s.update(pred(a=0.9, b=0.1))
    assert s.stable
    assert s.update(None) is None
    assert not s.stable
    out = s.update(pred(a=0.0, b=1.0))
    assert out.probabilities == pytest.approx({"a": 0.0, "b": 1.0})  # nada del pasado


def test_SMO_05_no_seguro_nunca_es_estable():
    clock = Clock()
    s = Smoother(window=1, threshold=0.9, hold_s=0.1, clock=clock)
    for t in (0.0, 1.0, 2.0):
        clock.t = t
        s.update(pred(a=0.6, b=0.4))
    assert not s.stable and s.stable_for_s == 0.0


@pytest.mark.parametrize("kwargs", [{"window": 0}, {"threshold": -0.1}, {"threshold": 1.5}])
def test_SMO_06_parametros_invalidos(kwargs):
    with pytest.raises(ValueError):
        Smoother(**kwargs)


def test_borde_clases_distintas_cuentan_como_cero():
    s = Smoother(window=2, threshold=0.0)
    s.update(pred(a=1.0))
    out = s.update(pred(b=1.0))
    assert out.probabilities == pytest.approx({"a": 0.5, "b": 0.5})
