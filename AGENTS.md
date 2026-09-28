# AGENTS.md — Reglas para cualquier asistente de IA (y para humanos)

Proyecto: **Meme Vision** — una persona imita un meme estático de un michi de TikTok
frente a la cámara y el sistema dice cuál imita, con un porcentaje. Es para una casa
abierta: gana el proyecto con más votos, así que la experiencia importa tanto como
la precisión.

Idioma: español en documentación, specs, commits y mensajes de UI. Los identificadores de código van en inglés.

## Pipeline

```text
camera.get_frame() -> np.ndarray | None
  -> landmarks.extract(frame) -> LandmarkResult         (MediaPipe Tasks API)
  -> features.transform(landmarks) -> np.ndarray (longitud fija, FEATURE_VERSION)
  -> classifier.predict(features) -> Prediction
  -> smoothing.update(prediction) -> Prediction | None
  -> game / ui.render(frame, state)
```

Todos los tipos compartidos viven en `src/memevision/contracts.py`.

## Mapa del repo

| Ruta | Qué hay |
|---|---|
| `specs/` | Specs SDD, una por módulo. **Fuente de verdad del comportamiento.** |
| `src/memevision/` | Código de la app |
| `scripts/` | `collect.py`, `train.py`, `evaluate.py`, `demo.py`, `check.sh` |
| `memes/inbox/` | Imágenes candidatas sin procesar |
| `memes/catalog/<id>/` | Memes elegidos: `reference.png` + `meme.yaml` |
| `tests/` | pytest; `tests/fixtures/` tiene landmarks grabados (sin cámara) |
| `docs/decisions/` | ADR: decisiones técnicas con su motivo |
| `data/raw/` | Nunca va a git |

## Flujo obligatorio (SDD + TDD)

1. Buscar la spec del módulo en `specs/`. Si no existe o está en `borrador`, **no se escribe código**: primero se escribe o se completa la spec.
2. Por cada criterio de aceptación (p. ej. `FEAT-01`), escribir un test **que falle**, con el ID en el nombre: `test_FEAT_01_...`.
3. Implementar lo mínimo para ponerlo en verde, y luego refactorizar.
4. Correr `bash scripts/check.sh` hasta que todo esté en verde.
5. Actualizar el estado de la spec y abrir un PR pequeño con la plantilla.

## Comandos

```bash
python3 -m venv .venv && source .venv/bin/activate   # Python >= 3.11
pip install -e ".[dev]"
bash scripts/check.sh          # ruff + format + pytest: el mismo que CI
pytest -m "not slow"           # tests rápidos
python scripts/demo.py         # app
```

## Prohibido

- Cambiar `contracts.py` o el orden/longitud del vector de features sin:
  subir `FEATURE_VERSION` + actualizar la spec 003 + escribir un ADR.
- Paths absolutos o concatenar rutas con strings: usar `pathlib.Path` relativo a la raíz.
- APIs exclusivas de Linux o macOS. Todo debe correr en Kubuntu y en la MacBook M2.
- Commitear `data/raw/`, videos, `.venv/` o imágenes de personas.
- Guardar fotos o videos de visitantes durante la feria (privacidad).
- Usar `mediapipe.solutions` (ya no existe en mediapipe 1.x) o instalar `opencv-python` (choca con `opencv-contrib-python`).
- Mezclar varias funcionalidades en un PR, o crear PR de más de ~400 líneas.
- Borrar o debilitar un test para que pase.
- Hacer merge de código que ninguna de las dos personas entiende.

## Definición de terminado

Spec en `implementada`, tests con los IDs de los criterios, `check.sh` en verde,
CI en verde (Ubuntu + macOS), PR revisado por la otra persona.
