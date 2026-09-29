"""Catálogo de memes: memes/catalog/<id>/{reference.png, meme.yaml} (spec 004)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

import cv2
import yaml

from memevision.config import CATALOG_DIR
from memevision.contracts import NEUTRAL, UNSURE, MemeSpec

REFERENCE = "reference.png"
META = "meme.yaml"
MAX_SIDE = 800
_ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class CatalogError(ValueError):
    """El catálogo tiene un meme mal formado."""


def load_catalog(catalog_dir: Path = CATALOG_DIR) -> dict[str, MemeSpec]:
    folders = sorted(
        p for p in Path(catalog_dir).iterdir() if p.is_dir() and not p.name.startswith(".")
    )
    return {folder.name: _load_meme(folder) for folder in folders}


def add_meme(
    image: Path,
    meme_id: str,
    name: str,
    catalog_dir: Path = CATALOG_DIR,
    caption: str = "",
    traits: Sequence[str] = (),
) -> MemeSpec:
    _check_id(meme_id, where=meme_id)
    folder = Path(catalog_dir) / meme_id
    if folder.exists():
        raise CatalogError(f"El meme {meme_id} ya existe en {folder}")
    img = cv2.imread(str(image), cv2.IMREAD_COLOR)
    if img is None:
        raise CatalogError(f"No se pudo leer la imagen {image}")
    scale = MAX_SIDE / max(img.shape[:2])
    if scale < 1:
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    folder.mkdir(parents=True)
    cv2.imwrite(str(folder / REFERENCE), img)
    data = {"id": meme_id, "name": name, "caption": caption, "traits": list(traits)}
    (folder / META).write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    return _load_meme(folder)


def _load_meme(folder: Path) -> MemeSpec:
    where = folder.name
    _check_id(folder.name, where)
    reference, meta = folder / REFERENCE, folder / META
    if not reference.exists():
        raise CatalogError(f"{where}: falta {REFERENCE}")
    if not meta.exists():
        raise CatalogError(f"{where}: falta {META}")
    data = yaml.safe_load(meta.read_text(encoding="utf-8")) or {}
    if data.get("id") != folder.name:
        raise CatalogError(
            f"{where}: el id del yaml ({data.get('id')!r}) no coincide con la carpeta"
        )
    if not data.get("name"):
        raise CatalogError(f"{where}: falta el campo name")
    return MemeSpec(
        id=folder.name,
        name=str(data["name"]),
        image_path=str(reference),
        caption=str(data.get("caption") or ""),
        traits=tuple(str(t) for t in data.get("traits") or ()),
    )


def _check_id(meme_id: str, where: str) -> None:
    if meme_id in (NEUTRAL, UNSURE):
        raise CatalogError(f"{where}: {meme_id!r} es un id reservado")
    if not _ID_RE.match(meme_id):
        raise CatalogError(f"{where}: id inválido; usa minúsculas, números y guiones")
