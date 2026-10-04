import json

import numpy as np
import pytest
from factories import LABELS, synthetic

from memevision.classifier import (
    MemeClassifier,
    ModelError,
    default_test_persons,
    split_by_person,
)
from memevision.contracts import Prediction
from memevision.features import FEATURE_NAMES

N = len(FEATURE_NAMES)


@pytest.fixture(scope="module")
def model() -> MemeClassifier:
    return MemeClassifier.fit(synthetic(), n_estimators=30)


def test_CLS_01_split_por_persona():
    df = synthetic()
    train, test = split_by_person(df, ["P03"])
    assert set(train["person"]) == {"P01", "P02"}
    assert set(test["person"]) == {"P03"}
    assert default_test_persons(df) == ["P03"]
    assert default_test_persons(synthetic(persons=("P01",))) == []


def test_CLS_02_predict_devuelve_prediction_coherente(model):
    x = synthetic(persons=("P09",), per_class=1, seed=5)[list(FEATURE_NAMES)].to_numpy()[0]
    pred = model.predict(x)
    assert isinstance(pred, Prediction)
    assert set(pred.probabilities) == set(LABELS)
    assert sum(pred.probabilities.values()) == pytest.approx(1.0)
    assert pred.meme == max(pred.probabilities, key=pred.probabilities.get)
    assert pred.confidence == pred.probabilities[pred.meme]


def test_CLS_03_guardar_y_cargar(model, tmp_path):
    X = synthetic(persons=("P09",), seed=7)[list(FEATURE_NAMES)].to_numpy()
    model.card.update(persons_test=["P03"], accuracy_unseen_person=0.9)
    model.save(tmp_path)

    loaded = MemeClassifier.load(tmp_path)

    np.testing.assert_array_equal(loaded.predict_batch(X), model.predict_batch(X))
    card = json.loads((tmp_path / "model_card.json").read_text())
    for key in (
        "feature_version",
        "classes",
        "persons_train",
        "persons_test",
        "samples_train",
        "samples_test",
        "accuracy_unseen_person",
        "n_estimators",
        "created",
    ):
        assert key in card
    assert card["classes"] == sorted(LABELS)


def test_CLS_04_otra_feature_version(model, tmp_path):
    model.save(tmp_path)
    card = json.loads((tmp_path / "model_card.json").read_text())
    card["feature_version"] = "0.1"
    (tmp_path / "model_card.json").write_text(json.dumps(card))
    with pytest.raises(ModelError, match="vuelve a entrenar"):
        MemeClassifier.load(tmp_path)


def test_CLS_05_vector_de_longitud_incorrecta(model):
    with pytest.raises(ValueError):
        model.predict(np.zeros(N + 1))


def test_CLS_06_acierta_con_persona_no_vista():
    df = synthetic(persons=("P01", "P02", "P03", "P04"))
    train, test = split_by_person(df, ["P04"])
    clf = MemeClassifier.fit(train, n_estimators=50)
    acc = (clf.predict_batch(test[list(FEATURE_NAMES)].to_numpy()) == test["label"]).mean()
    assert acc >= 0.95


def test_CLS_07_sin_modelo(tmp_path):
    with pytest.raises(ModelError, match="train.py"):
        MemeClassifier.load(tmp_path / "vacio")
