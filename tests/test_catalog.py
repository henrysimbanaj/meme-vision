from pathlib import Path

import cv2
import numpy as np
import pytest
import yaml

from memevision.catalog import CatalogError, add_meme, load_catalog


def _make_meme(root: Path, meme_id: str, **fields) -> Path:
    folder = root / meme_id
    folder.mkdir(parents=True)
    cv2.imwrite(str(folder / "reference.png"), np.zeros((10, 10, 3), dtype=np.uint8))
    data = {"id": meme_id, "name": meme_id.title(), **fields}
    (folder / "meme.yaml").write_text(yaml.safe_dump(data, allow_unicode=True))
    return folder


def test_CAT_01_carga_memes_validos_ordenados(tmp_path):
    _make_meme(tmp_path, "michi-b", caption="hola", traits=["brazos arriba"])
    _make_meme(tmp_path, "michi-a")
    (tmp_path / ".gitkeep").touch()

    catalog = load_catalog(tmp_path)

    assert list(catalog) == ["michi-a", "michi-b"]
    b = catalog["michi-b"]
    assert b.name == "Michi-B" and b.caption == "hola" and b.traits == ("brazos arriba",)
    assert Path(b.image_path) == tmp_path / "michi-b" / "reference.png"


def test_CAT_02_sin_reference_png(tmp_path):
    folder = _make_meme(tmp_path, "michi-a")
    (folder / "reference.png").unlink()
    with pytest.raises(CatalogError, match="michi-a"):
        load_catalog(tmp_path)


def test_CAT_03_id_distinto_a_la_carpeta(tmp_path):
    folder = _make_meme(tmp_path, "michi-a")
    (folder / "meme.yaml").write_text(yaml.safe_dump({"id": "otro", "name": "X"}))
    with pytest.raises(CatalogError, match="michi-a"):
        load_catalog(tmp_path)


def test_CAT_03_sin_name(tmp_path):
    folder = _make_meme(tmp_path, "michi-a")
    (folder / "meme.yaml").write_text(yaml.safe_dump({"id": "michi-a"}))
    with pytest.raises(CatalogError, match="name"):
        load_catalog(tmp_path)


@pytest.mark.parametrize("bad_id", ["Michi", "michi a", "neutral", "no_seguro"])
def test_CAT_04_id_invalido_o_reservado(tmp_path, bad_id):
    _make_meme(tmp_path, bad_id)
    with pytest.raises(CatalogError):
        load_catalog(tmp_path)


def test_CAT_05_add_meme_desde_inbox(tmp_path):
    image = tmp_path / "inbox" / "michi-nuevo.jpg"
    image.parent.mkdir()
    cv2.imwrite(str(image), np.full((1600, 1200, 3), 128, dtype=np.uint8))
    catalog_dir = tmp_path / "catalog"

    spec = add_meme(image, "michi-nuevo", "Michi Nuevo", catalog_dir, traits=["sonreír"])

    ref = catalog_dir / "michi-nuevo" / "reference.png"
    assert ref.exists()
    assert max(cv2.imread(str(ref)).shape[:2]) == 800
    assert load_catalog(catalog_dir) == {"michi-nuevo": spec}


def test_CAT_06_add_meme_con_id_existente_no_sobrescribe(tmp_path):
    folder = _make_meme(tmp_path, "michi-a")
    before = (folder / "meme.yaml").read_text()
    image = tmp_path / "x.png"
    cv2.imwrite(str(image), np.zeros((5, 5, 3), dtype=np.uint8))
    with pytest.raises(CatalogError, match="ya existe"):
        add_meme(image, "michi-a", "Otro", tmp_path)
    assert (folder / "meme.yaml").read_text() == before


def test_CAT_07_catalogo_real_del_repo_es_valido():
    catalog = load_catalog()
    assert len(catalog) >= 3
