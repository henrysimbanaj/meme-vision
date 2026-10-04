"""Sesiones de recolección en CSV + manifest, y carga del dataset (spec 005)."""

from __future__ import annotations

import csv
import logging
import re
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from memevision.catalog import load_catalog
from memevision.config import CATALOG_DIR, DATA_RAW_DIR
from memevision.contracts import NEUTRAL
from memevision.features import FEATURE_NAMES, FEATURE_VERSION

log = logging.getLogger(__name__)

META_COLUMNS = ("label", "person", "session", "feature_version")
MANIFEST_COLUMNS = ("session", "label", "person", "samples", "feature_version", "created")
_PERSON_RE = re.compile(r"^P\d{2,}$")


class DatasetError(ValueError):
    """Datos de recolección inválidos o ausentes."""


def valid_labels(catalog_dir: Path = CATALOG_DIR) -> set[str]:
    return {*load_catalog(catalog_dir), NEUTRAL}


class SessionWriter:
    """Acumula vectores de una sesión y los escribe al cerrar (así una sesión cancelada a medias
    con 0 muestras no deja archivos)."""

    def __init__(
        self,
        label: str,
        person: str,
        data_dir: Path = DATA_RAW_DIR,
        now: Callable[[], datetime] = datetime.now,
    ):
        if not _PERSON_RE.match(person):
            raise DatasetError(f"person debe ser un ID anónimo como P01, no {person!r}")
        if label not in valid_labels():
            raise DatasetError(f"{label!r} no está en el catálogo ni es {NEUTRAL!r}")
        self.label, self.person = label, person
        self.data_dir = Path(data_dir)
        self.created = now()
        self.session = f"{label}__{person}__{self.created:%Y%m%d-%H%M%S}"
        self._rows: list[np.ndarray] = []
        self._closed = False

    @property
    def samples(self) -> int:
        return len(self._rows)

    def add(self, features: np.ndarray) -> None:
        if features.shape != (len(FEATURE_NAMES),):
            raise DatasetError(
                f"vector de forma {features.shape}, se esperaba {len(FEATURE_NAMES)}"
            )
        self._rows.append(np.asarray(features, dtype=np.float32))

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if not self._rows:
            return
        sessions = self.data_dir / "sessions"
        sessions.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(np.vstack(self._rows), columns=list(FEATURE_NAMES))
        meta = {"label": self.label, "person": self.person, "session": self.session}
        for i, (col, value) in enumerate({**meta, "feature_version": FEATURE_VERSION}.items()):
            df.insert(i, col, value)
        df.to_csv(sessions / f"{self.session}.csv", index=False)
        self._append_manifest()

    def _append_manifest(self) -> None:
        manifest = self.data_dir / "manifest.csv"
        is_new = not manifest.exists()
        with manifest.open("a", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            if is_new:
                writer.writerow(MANIFEST_COLUMNS)
            writer.writerow(
                [
                    self.session,
                    self.label,
                    self.person,
                    self.samples,
                    FEATURE_VERSION,
                    self.created.isoformat(timespec="seconds"),
                ]
            )

    def __enter__(self) -> SessionWriter:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def load_dataset(
    data_dir: Path = DATA_RAW_DIR, feature_version: str = FEATURE_VERSION
) -> pd.DataFrame:
    """Todas las sesiones de `feature_version`: columnas META_COLUMNS + FEATURE_NAMES."""
    frames = []
    for path in sorted((Path(data_dir) / "sessions").glob("*.csv")):
        df = pd.read_csv(path, dtype={"feature_version": str, "person": str})
        if set(df["feature_version"]) != {feature_version}:
            log.warning("Se ignora %s: feature_version distinta de %s", path.name, feature_version)
            continue
        frames.append(df)
    if not frames:
        raise DatasetError(
            f"No hay sesiones con feature_version {feature_version} en {data_dir}: "
            "graba datos con scripts/collect.py"
        )
    return pd.concat(frames, ignore_index=True)[[*META_COLUMNS, *FEATURE_NAMES]]
