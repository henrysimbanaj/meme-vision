from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from memevision.dataset import DatasetError, SessionWriter, load_dataset
from memevision.features import FEATURE_NAMES, FEATURE_VERSION

N = len(FEATURE_NAMES)


def _clock(minute: int = 0):
    return lambda: datetime(2026, 9, 29, 15, minute, 0)


def _write(tmp_path, label="michi-fuerza", person="P01", samples=3, minute=0):
    with SessionWriter(label, person, tmp_path, now=_clock(minute)) as w:
        for i in range(samples):
            w.add(np.full(N, i, dtype=np.float32))
    return w


def test_DAT_01_csv_con_metadatos_y_features_en_orden(tmp_path):
    _write(tmp_path)
    files = list((tmp_path / "sessions").glob("*.csv"))
    assert [f.name for f in files] == ["michi-fuerza__P01__20260929-150000.csv"]
    df = pd.read_csv(files[0])
    assert list(df.columns) == ["label", "person", "session", "feature_version", *FEATURE_NAMES]
    assert len(df) == 3
    assert set(df["feature_version"].astype(str)) == {FEATURE_VERSION}


def test_DAT_02_manifest_acumula_sesiones(tmp_path):
    _write(tmp_path, minute=0)
    _write(tmp_path, label="neutral", person="P02", samples=5, minute=1)
    manifest = pd.read_csv(tmp_path / "manifest.csv")
    assert list(manifest["samples"]) == [3, 5]
    assert list(manifest["label"]) == ["michi-fuerza", "neutral"]


@pytest.mark.parametrize("person", ["Henry", "p01", "P1", ""])
def test_DAT_03_person_debe_ser_anonimo(tmp_path, person):
    with pytest.raises(DatasetError, match="P01"):
        SessionWriter("michi-fuerza", person, tmp_path)


def test_DAT_04_label_desconocido(tmp_path):
    with pytest.raises(DatasetError, match="catálogo"):
        SessionWriter("meme-que-no-existe", "P01", tmp_path)


def test_DAT_05_sesion_vacia_no_deja_rastro(tmp_path):
    _write(tmp_path, samples=0)
    assert not list(tmp_path.rglob("*.csv"))


def test_DAT_06_load_dataset_une_sesiones_de_la_version(tmp_path, caplog):
    _write(tmp_path, minute=0)
    _write(tmp_path, label="neutral", person="P02", samples=2, minute=1)
    old = tmp_path / "sessions" / "viejo.csv"
    pd.DataFrame(
        {
            "label": ["neutral"],
            "person": ["P03"],
            "session": ["x"],
            "feature_version": ["0.9"],
            "a": [1],
        }
    ).to_csv(old, index=False)

    df = load_dataset(tmp_path)

    assert len(df) == 5
    assert set(df["person"]) == {"P01", "P02"}
    assert list(df.columns[4:]) == list(FEATURE_NAMES)
    assert "viejo.csv" in caplog.text


def test_DAT_06_sin_datos_error_claro(tmp_path):
    with pytest.raises(DatasetError, match="collect.py"):
        load_dataset(tmp_path)
