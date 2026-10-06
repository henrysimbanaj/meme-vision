# 004 — Catálogo de memes

- **Estado:** implementada
- **Owner:** Compañera (implementado por Henry para el MVP; revisa la compañera)
- **Archivos:** `src/memevision/catalog.py`, `scripts/add_meme.py`, `tests/test_catalog.py`, `memes/catalog/`

## Propósito
Cargar y validar `memes/catalog/<id>/` (`reference.png` + `meme.yaml`) y definir el flujo inbox → catalog,
para que agregar un meme nuevo sea un solo comando.

## Formato de `meme.yaml`
```yaml
id: michi-fuerza            # igual al nombre de la carpeta; minúsculas, números y guiones
name: Michi Fuerza          # lo que se muestra en la UI
caption: "¡Mira estos músculos!"   # frase corta para la UI (opcional)
traits:                     # cómo imitarlo; la UI lo muestra como pista (opcional)
  - Los dos brazos arriba
  - Puños cerrados
```

## Contrato
```python
class CatalogError(ValueError): ...
def load_catalog(catalog_dir: Path = CATALOG_DIR) -> dict[str, MemeSpec]   # ordenado por id
def add_meme(image: Path, meme_id: str, name: str, catalog_dir: Path = CATALOG_DIR,
             caption: str = "", traits: Sequence[str] = ()) -> MemeSpec
```
`MemeSpec.image_path` es la ruta al `reference.png` (como texto).

## Criterios de aceptación
- `CAT-01` Dado un catálogo con 2 memes válidos, cuando llamo `load_catalog`, entonces obtengo 2 `MemeSpec` ordenados por id, con sus campos del yaml.
- `CAT-02` Dada una carpeta sin `reference.png`, entonces se lanza `CatalogError` que nombra la carpeta.
- `CAT-03` Dado un `meme.yaml` cuyo `id` no coincide con la carpeta, o sin `name`, entonces `CatalogError`.
- `CAT-04` Un id inválido (mayúsculas, espacios) o reservado (`neutral`, `no_seguro`) → `CatalogError`.
- `CAT-05` Dada una imagen `.jpg` del inbox, `add_meme` crea `<id>/reference.png` y un `meme.yaml` que `load_catalog` acepta.
- `CAT-06` `add_meme` con un id que ya existe → `CatalogError` sin tocar lo existente.
- `CAT-07` El catálogo real del repo carga sin errores y tiene al menos 3 memes.

## Casos borde
- Archivos sueltos o carpetas ocultas dentro de `catalog/` se ignoran (p. ej. `.gitkeep`).
- `add_meme` reduce la imagen a 800 px de lado como máximo para no inflar el repo.

## Fuera de alcance
Editar memes desde la UI.

## Tareas
- [x] `catalog.py` + tests CAT-01..07
- [x] `scripts/add_meme.py`
- [x] Pasar los 4 memes iniciales a `memes/catalog/`
