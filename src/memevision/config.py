"""Rutas y parámetros compartidos. Las rutas salen de la raíz del repo, nunca a mano."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "models"
CATALOG_DIR = ROOT / "memes" / "catalog"
DATA_RAW_DIR = ROOT / "data" / "raw"
DATA_PROCESSED_DIR = ROOT / "data" / "processed"
