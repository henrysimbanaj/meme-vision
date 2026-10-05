# 002 — Extracción de landmarks

- **Estado:** implementada
- **Owner:** Henry
- **Archivos:** `src/memevision/landmarks.py`, `src/memevision/config.py`, `scripts/download_models.py`, `tests/test_landmarks.py`

## Propósito
Convertir un frame en coordenadas del cuerpo, las manos y la cara, más los blendshapes faciales,
usando la **MediaPipe Tasks API**. Se usa `HolisticLandmarker` (un solo modelo, ver ADR-002):
asigna cada mano al cuerpo de la persona y entrega los 52 blendshapes con `output_face_blendshapes=True`.
El `BaseOptions.delegate` es siempre `CPU`: en macOS el arranque sin delegado abre Metal y aborta.

## Contrato
```python
MODEL_URLS: dict[str, str]          # nombre de archivo .task -> URL oficial

class LandmarkDetector:
    def __init__(self, models_dir: Path = MODELS_DIR, mirrored: bool = True, backend=None): ...
    def extract(self, frame: np.ndarray, timestamp_ms: int | None = None) -> LandmarkResult
    def close(self) -> None
    # es context manager
```
- `frame`: BGR `uint8`, tal como lo entrega `Camera`.
- `mirrored=True` significa que el frame viene espejado (como lo entrega `Camera` por defecto).
- Las coordenadas del resultado están en el sistema del frame **recibido**, para poder dibujarlas encima.
- `timestamp_ms=None` → se genera uno creciente automáticamente (el modo VIDEO lo exige).
- `backend` es inyectable para los tests: una función `(rgb: np.ndarray, timestamp_ms: int) -> resultado crudo`.

## Criterios de aceptación
- `LMK-01` Dado un resultado crudo vacío (nadie en cuadro), cuando llamo `extract`, entonces `has_person` es `False` y todas las partes son `None`.
- `LMK-02` Dado un resultado crudo con pose, manos, cara y blendshapes, entonces `pose.shape == (33, 3)`, cada mano `(21, 3)`, `face.shape == (478, 3)` y `face_blendshapes` tiene sus claves con valores en `[0, 1]` (sin la clave `_neutral`).
- `LMK-03` Las manos se asignan **desde el punto de vista de la persona**. Con `mirrored=True`, el detector recibe el frame desespejado (la vista real de la cámara) y las `x` del resultado se convierten con `1 - x` para coincidir con el frame espejado.
- `LMK-04` Si falta el archivo `.task`, se lanza `FileNotFoundError` con el mensaje "ejecuta `python scripts/download_models.py`".
- `LMK-05` (slow) Con el modelo real, un frame negro da `has_person == False`, y el promedio de `extract` sobre 30 frames de 640x480 es < 80 ms.
- `LMK-06` Los timestamps generados automáticamente son estrictamente crecientes, aunque se llame más de una vez en el mismo milisegundo.

## Casos borde
- Hay dos personas en cuadro → Holistic sigue a una sola (la que detecta primero). Se documenta; no se controla.
- Una sola mano visible → la otra es `None`.

## Fuera de alcance
Seguimiento de varias personas.

## Tareas
- [x] Spike en Kubuntu (ADR-002) · [ ] confirmar en la Mac
- [x] `download_models.py` (URL oficial del `.task` de Holistic)
- [x] Tests LMK-01..04, LMK-06 (rápidos, con backend falso) y LMK-05 (`@pytest.mark.slow`)
- [ ] Guardar JSON de landmarks reales en `tests/fixtures/landmarks/` cuando haya datos (spec 005)
