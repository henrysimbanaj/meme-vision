import cv2
import numpy as np
import pytest
from factories import synthetic

from memevision.evaluation import EvalError, evaluate_lopo, lopo_folds, report, save_confusion_png


def test_EVA_01_un_fold_por_persona_sin_fuga():
    df = synthetic(persons=("P01", "P02", "P03"), per_class=5)
    folds = list(lopo_folds(df))
    assert [p for p, _, _ in folds] == ["P01", "P02", "P03"]
    for person, train, test in folds:
        assert person not in set(train["person"])
        assert set(test["person"]) == {person}


def test_EVA_02_metricas_conocidas():
    y_true = ["a", "a", "b", "b"]
    y_pred = ["a", "b", "b", "b"]
    rep = report(y_true, y_pred, persons=["P01", "P01", "P02", "P02"])
    assert rep.labels == ["a", "b"]
    assert rep.accuracy == pytest.approx(0.75)
    np.testing.assert_array_equal(rep.confusion, [[1, 1], [0, 2]])
    assert rep.per_person == {"P01": 0.5, "P02": 1.0}
    assert rep.per_class["b"]["recall"] == pytest.approx(1.0)


def test_EVA_03_umbral_de_aceptacion():
    assert report(["a"] * 5, ["a"] * 4 + ["b"], ["P01"] * 5).passed is True  # 0.80
    assert report(["a"] * 5, ["a"] * 3 + ["b"] * 2, ["P01"] * 5).passed is False


def test_EVA_04_top_confusions_ordenadas():
    y_true = ["a", "a", "a", "b", "c", "c"]
    y_pred = ["b", "b", "a", "c", "a", "c"]
    rep = report(y_true, y_pred, ["P01"] * 6)
    assert rep.top_confusions(2) == [("a", "b", 2), ("b", "c", 1)]


def test_EVA_05_png_de_la_matriz(tmp_path):
    rep = report(["a", "b"], ["a", "a"], ["P01", "P01"])
    path = tmp_path / "sub" / "confusion.png"
    save_confusion_png(rep, path)
    img = cv2.imread(str(path))
    assert img is not None and img.shape[0] > 100


def test_EVA_06_una_sola_persona():
    with pytest.raises(EvalError, match="2 personas"):
        evaluate_lopo(synthetic(persons=("P01",), per_class=5))


def test_evaluate_lopo_con_datos_separables():
    rep = evaluate_lopo(synthetic(persons=("P01", "P02", "P03"), per_class=20), n_estimators=20)
    assert rep.passed
    assert set(rep.per_person) == {"P01", "P02", "P03"}
