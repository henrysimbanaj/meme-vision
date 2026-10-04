# 008 — Suavizado temporal

- **Estado:** implementada
- **Owner:** Henry
- **Archivos:** `src/memevision/smoothing.py`, `tests/test_smoothing.py`

## Propósito
Una predicción por frame "parpadea". El suavizador promedia las probabilidades de los últimos N
frames, dice "No estoy seguro" si la confianza promedio es baja y marca el resultado como
**estable** cuando el mismo meme se mantiene durante un tiempo mínimo.

## Contrato
```python
class Smoother:
    def __init__(self, window: int = 15, threshold: float = 0.65, hold_s: float = 0.7,
                 clock: Callable[[], float] = time.monotonic): ...
    def update(self, prediction: Prediction | None) -> Prediction | None
    stable: bool          # el mismo meme (no UNSURE) lleva >= hold_s
    stable_for_s: float   # cuánto lleva el meme actual (0 si es UNSURE o no hay)
    def reset(self) -> None
```
- `update(None)` significa "no hay persona": vacía el buffer y devuelve `None`.
- Si el promedio del mejor meme es < `threshold`, devuelve `Prediction(UNSURE, conf, probs)`.

## Criterios de aceptación
- `SMO-01` Las probabilidades devueltas son el promedio de las últimas `window` predicciones; las más viejas salen del buffer.
- `SMO-02` Si la confianza promedio es menor que `threshold`, `meme == UNSURE`, conservando `confidence` y `probabilities`.
- `SMO-03` Con el mismo meme durante ≥ `hold_s`, `stable` pasa a `True`; si cambia el meme, el tiempo vuelve a 0.
- `SMO-04` `update(None)` vacía el buffer, devuelve `None` y `stable` es `False`.
- `SMO-05` `UNSURE` nunca es estable.
- `SMO-06` `window < 1` o `threshold` fuera de `[0, 1]` lanzan `ValueError`.

## Casos borde
- Predicciones con clases distintas (modelo recargado) → las clases que faltan cuentan como 0.

## Fuera de alcance
Filtros más sofisticados (Kalman, histéresis por clase).

## Tareas
- [x] Tests SMO-01..06 con reloj inyectable
