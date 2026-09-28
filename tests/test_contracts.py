import numpy as np
import pytest

from memevision.contracts import LandmarkResult, Prediction


def test_landmark_result_sin_pose_no_tiene_persona():
    assert LandmarkResult().has_person is False


def test_landmark_result_con_pose_tiene_persona():
    assert LandmarkResult(pose=np.zeros((33, 3))).has_person is True


def test_prediction_rechaza_confianza_fuera_de_rango():
    with pytest.raises(ValueError):
        Prediction(meme="x", confidence=1.2)


def test_prediction_top_ordena_por_probabilidad():
    p = Prediction("b", 0.6, {"a": 0.1, "b": 0.6, "c": 0.3})
    assert p.top(2) == [("b", 0.6), ("c", 0.3)]
