# 002 — Extracción de landmarks

- **Estado:** borrador (spike OK en Kubuntu, ver ADR-002)
- **Owner:** Henry
- **Archivos:** `src/memevision/landmarks.py`, `scripts/download_models.py`, `tests/test_landmarks.py`

## Propósito
Convertir un frame en coordenadas del cuerpo, las manos y la cara, más los blendshapes faciales,
usando la **MediaPipe Tasks API** (PoseLandmarker, HandLandmarker y FaceLandmarker con
`output_face_blendshapes=True`).

## Contrato
```python
class LandmarkDetector:
    def __init__(self, models_dir: Path = MODELS_DIR): ...
    def extract(self, frame: np.ndarray, timestamp_ms: int | None = None) -> LandmarkResult
    def close(self) -> None
```
`LandmarkResult` está definido en `contracts.py`. Las partes que no se detectan valen `None`.

## Criterios de aceptación
- `LMK-01` Dado un frame negro, cuando llamo `extract`, entonces `result.has_person` es `False` y todas las partes son `None`.
- `LMK-02` Dada la foto de fixture de una persona con el torso visible, entonces `pose.shape == (33, 3)` y `face_blendshapes` tiene 52 claves con valores en `[0, 1]`.
- `LMK-03` La mano se asigna a `left_hand` o `right_hand` **desde el punto de vista de la persona**, con un criterio consistente para el frame espejado. Se documenta en el código.
- `LMK-04` Si faltan los archivos `.task`, se lanza `FileNotFoundError` con el mensaje "ejecuta `python scripts/download_models.py`".
- `LMK-05` (slow) En la máquina más lenta, el promedio de `extract` sobre 30 frames de 640x480 es < 80 ms.

## Casos borde
- Hay dos personas en cuadro → se usa la de mayor tamaño (y se documenta).
- Una sola mano visible.

## Fuera de alcance
Seguimiento de varias personas.

## Tareas
- [x] Spike en Kubuntu (ADR-002) · [ ] confirmar en la Mac
- [ ] `download_models.py` (URLs oficiales de los `.task`)
- [ ] Tests LMK-01, LMK-04 (rápidos) y LMK-02, LMK-05 (`@pytest.mark.slow`)
- [ ] Guardar JSON de landmarks reales en `tests/fixtures/landmarks/` para la spec 003
