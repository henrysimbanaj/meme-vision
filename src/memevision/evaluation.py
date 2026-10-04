"""Evaluación leave-one-person-out, métricas y matriz de confusión (spec 007)."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from memevision.classifier import MemeClassifier
from memevision.features import FEATURE_NAMES

ACCEPTANCE = 0.80


class EvalError(ValueError):
    """No se puede evaluar con estos datos."""


@dataclass
class EvalReport:
    labels: list[str]
    accuracy: float
    per_class: dict[str, dict[str, float]]
    per_person: dict[str, float]
    confusion: np.ndarray
    passed: bool

    def top_confusions(self, k: int = 3) -> list[tuple[str, str, int]]:
        errors = [
            (self.labels[i], self.labels[j], int(self.confusion[i, j]))
            for i in range(len(self.labels))
            for j in range(len(self.labels))
            if i != j and self.confusion[i, j] > 0
        ]
        return sorted(errors, key=lambda e: e[2], reverse=True)[:k]

    def to_dict(self) -> dict:
        return {
            "accuracy": self.accuracy,
            "passed": self.passed,
            "acceptance": ACCEPTANCE,
            "labels": self.labels,
            "per_class": self.per_class,
            "per_person": self.per_person,
            "confusion": self.confusion.tolist(),
            "top_confusions": self.top_confusions(),
        }


def lopo_folds(df: pd.DataFrame) -> Iterator[tuple[str, pd.DataFrame, pd.DataFrame]]:
    for person in sorted(df["person"].unique()):
        is_test = df["person"] == person
        yield person, df[~is_test], df[is_test]


def report(y_true: Sequence[str], y_pred: Sequence[str], persons: Sequence[str]) -> EvalReport:
    y_true, y_pred, persons = np.asarray(y_true), np.asarray(y_pred), np.asarray(persons)
    labels = sorted(set(y_true) | set(y_pred))
    raw = classification_report(y_true, y_pred, labels=labels, output_dict=True, zero_division=0)
    per_class = {label: {k: float(v) for k, v in raw[label].items()} for label in labels}
    per_person = {
        str(p): float((y_true[persons == p] == y_pred[persons == p]).mean())
        for p in sorted(set(persons))
    }
    accuracy = float(accuracy_score(y_true, y_pred))
    return EvalReport(
        labels=labels,
        accuracy=accuracy,
        per_class=per_class,
        per_person=per_person,
        confusion=confusion_matrix(y_true, y_pred, labels=labels),
        passed=accuracy >= ACCEPTANCE,
    )


def evaluate_lopo(df: pd.DataFrame, n_estimators: int = 300) -> EvalReport:
    if df["person"].nunique() < 2:
        raise EvalError("Se necesitan al menos 2 personas para probar con alguien no visto")
    y_true, y_pred, persons = [], [], []
    for person, train, test in lopo_folds(df):
        clf = MemeClassifier.fit(train, n_estimators=n_estimators)
        y_pred.extend(clf.predict_batch(test[list(FEATURE_NAMES)].to_numpy()))
        y_true.extend(test["label"])
        persons.extend([person] * len(test))
    return report(y_true, y_pred, persons)


def save_confusion_png(rep: EvalReport, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")  # sin ventana: funciona igual en CI, Kubuntu y macOS
    import matplotlib.pyplot as plt

    n = len(rep.labels)
    fig, ax = plt.subplots(figsize=(1.4 * n + 3, 1.2 * n + 2.5))
    ax.imshow(rep.confusion, cmap="Blues")
    ax.set_xticks(range(n), rep.labels, rotation=35, ha="right")
    ax.set_yticks(range(n), rep.labels)
    ax.set_xlabel("Predicho")
    ax.set_ylabel("Real")
    ax.set_title(f"Matriz de confusión · accuracy LOPO {rep.accuracy:.1%}")
    top = rep.confusion.max() or 1
    for i in range(n):
        for j in range(n):
            value = int(rep.confusion[i, j])
            color = "white" if value > top / 2 else "black"
            ax.text(j, i, str(value), ha="center", va="center", color=color)
    fig.tight_layout()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)
