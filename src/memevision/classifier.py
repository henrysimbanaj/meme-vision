"""Random Forest sobre el vector de features, con model card (spec 006, ADR-001)."""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from memevision.config import MODELS_DIR
from memevision.contracts import Prediction
from memevision.features import FEATURE_NAMES, FEATURE_VERSION

MODEL_DIR = MODELS_DIR / "meme_classifier"
MODEL_FILE = "model.joblib"
CARD_FILE = "model_card.json"


class ModelError(RuntimeError):
    """No hay un modelo utilizable."""


def split_by_person(
    df: pd.DataFrame, test_persons: Sequence[str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    is_test = df["person"].isin(list(test_persons))
    return df[~is_test], df[is_test]


def default_test_persons(df: pd.DataFrame) -> list[str]:
    persons = sorted(df["person"].unique())
    return persons[-1:] if len(persons) >= 2 else []


def _xy(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    return df[list(FEATURE_NAMES)].to_numpy(dtype=np.float32), df["label"].to_numpy()


class MemeClassifier:
    def __init__(self, estimator: RandomForestClassifier, card: dict[str, Any]):
        self._estimator = estimator
        self.card = card
        self.classes: tuple[str, ...] = tuple(str(c) for c in estimator.classes_)

    @classmethod
    def fit(
        cls, df: pd.DataFrame, n_estimators: int = 300, random_state: int = 42
    ) -> MemeClassifier:
        X, y = _xy(df)
        estimator = RandomForestClassifier(
            n_estimators=n_estimators, random_state=random_state, n_jobs=-1
        )
        estimator.fit(X, y)
        estimator.n_jobs = 1  # para predecir de a un frame, un solo hilo es más rápido
        card = {
            "feature_version": FEATURE_VERSION,
            "classes": sorted(str(c) for c in estimator.classes_),
            "persons_train": sorted(df["person"].unique().tolist()),
            "persons_test": [],
            "samples_train": len(df),
            "samples_test": 0,
            "accuracy_unseen_person": None,
            "n_estimators": n_estimators,
            "created": datetime.now().isoformat(timespec="seconds"),
        }
        return cls(estimator, card)

    def predict(self, features: np.ndarray) -> Prediction:
        x = np.asarray(features, dtype=np.float32)
        if x.shape != (len(FEATURE_NAMES),):
            raise ValueError(f"vector de forma {x.shape}, se esperaba ({len(FEATURE_NAMES)},)")
        proba = self._estimator.predict_proba(x[None, :])[0]
        probabilities = {c: float(p) for c, p in zip(self.classes, proba, strict=True)}
        best = int(np.argmax(proba))
        return Prediction(self.classes[best], float(proba[best]), probabilities)

    def predict_batch(self, X: np.ndarray) -> np.ndarray:
        return self._estimator.predict(np.asarray(X, dtype=np.float32))

    def save(self, model_dir: Path = MODEL_DIR) -> None:
        model_dir = Path(model_dir)
        model_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._estimator, model_dir / MODEL_FILE)
        card_text = json.dumps(self.card, indent=2, ensure_ascii=False) + "\n"
        (model_dir / CARD_FILE).write_text(card_text, encoding="utf-8")

    @classmethod
    def load(cls, model_dir: Path = MODEL_DIR) -> MemeClassifier:
        model_dir = Path(model_dir)
        model_path, card_path = model_dir / MODEL_FILE, model_dir / CARD_FILE
        if not model_path.exists() or not card_path.exists():
            raise ModelError(f"No hay modelo en {model_dir}: entrena con `python scripts/train.py`")
        card = json.loads(card_path.read_text(encoding="utf-8"))
        if card.get("feature_version") != FEATURE_VERSION:
            raise ModelError(
                f"El modelo usa features v{card.get('feature_version')} y el código "
                f"v{FEATURE_VERSION}: vuelve a entrenar con `python scripts/train.py`"
            )
        return cls(joblib.load(model_path), card)
