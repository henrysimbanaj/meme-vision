# 005 — Dataset y recolector

- **Estado:** implementada
- **Owner:** Compañera (implementado por Henry para el MVP; revisa la compañera)
- **Archivos:** `src/memevision/dataset.py`, `src/memevision/collector.py`, `scripts/collect.py`,
  `tests/test_dataset.py`, `tests/test_collector.py`

## Propósito
`python scripts/collect.py <meme_id> --person P01` abre la cámara, muestra el meme, hace una cuenta
regresiva y graba **vectores de features** (nunca imágenes) durante unos segundos. Cada grabación
es una sesión: un CSV propio más una fila en el manifest.

## Formato en disco (`data/raw/`, nunca va a git)
```text
data/raw/sessions/<label>__<person>__<YYYYmmdd-HHMMSS>.csv
    columnas: label, person, session, feature_version, <FEATURE_NAMES...>
data/raw/manifest.csv
    columnas: session, label, person, samples, feature_version, created
```
Los CSV no tienen fotos ni nombres; solo números y el ID anónimo de la persona.

## Contrato
```python
class DatasetError(ValueError): ...
class SessionWriter:            # context manager
    def __init__(self, label: str, person: str, data_dir: Path = DATA_RAW_DIR, now=datetime.now): ...
    def add(self, features: np.ndarray) -> None
    def close(self) -> None      # escribe el CSV y la fila del manifest (si hay muestras)
    samples: int
def load_dataset(data_dir: Path = DATA_RAW_DIR, feature_version: str = FEATURE_VERSION) -> pd.DataFrame

# collector.py: el bucle, sin ventanas, para poder probarlo
def run_collection(camera, detector, writer, countdown_s, duration_s, show, clock=time.monotonic) -> int
```
`show(frame, state)` dibuja; si devuelve `False` se cancela. `state` tiene `phase`
(`countdown` | `recording`), `remaining_s`, `samples` y `person_visible`.

## Criterios de aceptación
- `DAT-01` Dadas 3 muestras, al cerrar el `SessionWriter` hay un CSV con 3 filas, las columnas `label, person, session, feature_version` y luego `FEATURE_NAMES` en orden.
- `DAT-02` Al cerrar, el manifest gana una fila con `samples = 3`; si ya existía, se conserva lo anterior.
- `DAT-03` Un `person` que no sigue el formato `P01`, `P02`… lanza `DatasetError` (evita nombres reales).
- `DAT-04` Un `label` que no está en el catálogo ni es `neutral` lanza `DatasetError`.
- `DAT-05` Una sesión cerrada sin muestras no deja CSV ni fila en el manifest.
- `DAT-06` `load_dataset` une todas las sesiones de la versión pedida e ignora (con aviso) las de otra `feature_version`.
- `DAT-07` `run_collection` no guarda nada durante la cuenta regresiva y luego guarda un vector por cada frame con persona, hasta que se acaba el tiempo.
- `DAT-08` Los frames sin persona no se guardan y `person_visible` es `False` en el estado.
- `DAT-09` Si `show` devuelve `False`, `run_collection` termina y devuelve cuántas muestras guardó.

## Guía de recolección (para las personas)
- 3 s de cuenta regresiva y 20 s de grabación por sesión (≈ 400–600 vectores a 25 fps).
- Durante la grabación, variar un poco: más cerca/lejos, girar unos grados, mover ligeramente los brazos.
- Por cada meme y persona: al menos 2 sesiones. Grabar también `neutral` (parado, rascarse, cruzar brazos).

## Casos borde
- El meme no existe en el catálogo → error antes de abrir la cámara.
- La cámara no da frames → la grabación se corta al terminar el tiempo, sin guardar nada.

## Fuera de alcance
Editar o borrar sesiones desde el script (se borra el CSV y su fila del manifest a mano).

## Tareas
- [x] `dataset.py` + tests DAT-01..06
- [x] `collector.py` + tests DAT-07..09 con cámara, detector y reloj falsos
- [x] `scripts/collect.py` (ventana OpenCV)
