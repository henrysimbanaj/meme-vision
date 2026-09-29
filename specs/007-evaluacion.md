# 007 — Evaluación

- **Estado:** implementada
- **Owner:** Compañera (implementado por Henry para el MVP; revisa la compañera)
- **Archivos:** `src/memevision/evaluation.py`, `scripts/evaluate.py`, `tests/test_evaluation.py`

## Propósito
Medir qué tan bien reconoce el modelo a **personas que nunca vio**, con leave-one-person-out
(LOPO): por cada persona, se entrena con las demás y se prueba con ella. Muestra accuracy,
F1 por clase, la matriz de confusión en PNG y los pares de memes que más se confunden.

**Umbral de aceptación del MVP:** accuracy LOPO ≥ 0.80.

## Contrato
```python
class EvalError(ValueError): ...
@dataclass
class EvalReport:
    labels: list[str]
    accuracy: float
    per_class: dict[str, dict[str, float]]   # precision, recall, f1, support
    per_person: dict[str, float]             # accuracy de cada persona no vista
    confusion: np.ndarray                    # filas = real, columnas = predicho (orden de labels)
    passed: bool                             # accuracy >= ACCEPTANCE
    def top_confusions(self, k: int = 3) -> list[tuple[str, str, int]]   # (real, predicho, n)

def lopo_folds(df) -> Iterator[tuple[str, pd.DataFrame, pd.DataFrame]]
def report(y_true, y_pred, persons) -> EvalReport
def evaluate_lopo(df, n_estimators=300) -> EvalReport
def save_confusion_png(rep: EvalReport, path: Path) -> None
```

## Criterios de aceptación
- `EVA-01` `lopo_folds` da un fold por persona, y en cada uno la persona de prueba no está en train.
- `EVA-02` Con `y_true`/`y_pred` conocidos, `report` calcula bien accuracy, la matriz de confusión y la accuracy por persona.
- `EVA-03` `passed` es `True` solo si la accuracy es ≥ 0.80.
- `EVA-04` `top_confusions` devuelve los errores (fuera de la diagonal) ordenados de mayor a menor.
- `EVA-05` `save_confusion_png` crea un PNG válido.
- `EVA-06` Con menos de 2 personas, `evaluate_lopo` lanza `EvalError` con un mensaje claro.

## `scripts/evaluate.py`
Imprime el resumen y guarda `reports/confusion_matrix.png` y `reports/evaluation.json`
(solo números y IDs anónimos, pueden ir a git).

## Fuera de alcance
Comparar varios algoritmos (después del MVP).

## Tareas
- [x] Tests EVA-01..06
- [x] `scripts/evaluate.py`
