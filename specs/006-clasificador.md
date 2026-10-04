# 006 — Clasificador

- **Estado:** implementada
- **Owner:** Henry
- **Archivos:** `src/memevision/classifier.py`, `scripts/train.py`, `tests/test_classifier.py`

## Propósito
Entrenar un Random Forest (ADR-001) con los vectores del dataset, medirlo con **personas no vistas**
y guardarlo junto a una `model_card.json`. En la app, `predict(features) -> Prediction`.

## Contrato
```python
class ModelError(RuntimeError): ...
def split_by_person(df, test_persons: Sequence[str]) -> tuple[pd.DataFrame, pd.DataFrame]
def default_test_persons(df) -> list[str]   # la última persona (orden alfabético) si hay ≥ 2

class MemeClassifier:
    classes: tuple[str, ...]
    card: dict                     # contenido de model_card.json
    @classmethod
    def fit(cls, df, n_estimators=300, random_state=42) -> MemeClassifier
    def predict(self, features: np.ndarray) -> Prediction     # vector de len(FEATURE_NAMES)
    def predict_batch(self, X: np.ndarray) -> np.ndarray      # etiquetas
    def save(self, model_dir: Path = MODEL_DIR) -> None       # model.joblib + model_card.json
    @classmethod
    def load(cls, model_dir: Path = MODEL_DIR) -> MemeClassifier
```
`MODEL_DIR = models/meme_classifier/`. El `.joblib` no va a git; la `model_card.json` sí puede ir.

## `model_card.json`
`feature_version`, `classes`, `persons_train`, `persons_test`, `samples_train`, `samples_test`,
`accuracy_unseen_person` (o `null` si no hubo personas de prueba), `n_estimators`, `created`.

El modelo guardado se entrena con **todas** las personas; `persons_test`, `samples_test` y
`accuracy_unseen_person` describen la medición previa, en la que esas personas quedaron fuera.

## Criterios de aceptación
- `CLS-01` `split_by_person` nunca deja a una misma persona en train y en test.
- `CLS-02` `predict` devuelve un `Prediction` cuyas probabilidades suman 1, `meme` es la de mayor probabilidad y `confidence` es su valor.
- `CLS-03` Guardar y cargar da las mismas predicciones, y la `model_card.json` tiene los campos de arriba.
- `CLS-04` Cargar un modelo con otra `feature_version` lanza `ModelError` que dice "vuelve a entrenar".
- `CLS-05` Un vector de longitud incorrecta lanza `ValueError`.
- `CLS-06` Con datos sintéticos separables, el modelo acierta ≥ 95 % con una persona no vista.
- `CLS-07` Si no hay modelo guardado, `load` lanza `ModelError` que menciona `scripts/train.py`.

## `scripts/train.py`
1. Carga el dataset (spec 005) y aparta las personas de prueba (`--test-person`, repetible; por defecto la última).
2. Entrena con el resto y mide la precisión con las personas apartadas.
3. Vuelve a entrenar con **todas** las personas (el modelo final usa todos los datos) y guarda con la card.

## Casos borde
- Una sola persona en el dataset → se entrena sin prueba y la card lo dice (`accuracy_unseen_person: null`) con un aviso.
- Una clase sin muestras en train → aviso; el modelo no podrá predecirla.

## Fuera de alcance
Comparar con k-NN, SVM o MLP (se hace después del MVP).

## Tareas
- [x] Tests CLS-01..07 con datos sintéticos
- [x] `scripts/train.py`
