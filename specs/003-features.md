# 003 — Extracción de características

- **Estado:** implementada
- **Owner:** Henry
- **Archivos:** `src/memevision/features.py`, `tests/test_features.py`, `tests/factories.py`,
  `tests/fixtures/features/v<FEATURE_VERSION>.json`

## Propósito
Transformar un `LandmarkResult` en un vector numérico de **longitud fija** que no dependa de
la distancia a la cámara ni de la posición o la altura de la persona.

## Contrato
```python
FEATURE_VERSION: str            # "1.0"; se sube en cualquier cambio de orden o de longitud
FEATURE_NAMES: tuple[str, ...]  # nombre de cada columna, en orden
class NoPersonError(ValueError): ...
def transform(lm: LandmarkResult) -> np.ndarray   # shape (len(FEATURE_NAMES),), float32, sin NaN
```

## Normalización
- Origen: punto medio de los hombros. Escala: distancia entre hombros (en `x, y`).
- Todas las posiciones y distancias se dividen por esa escala. Los ángulos van en **radianes**.
- `left`/`right` son de la persona (spec 002), así que el vector no cambia con el espejo de la UI
  salvo por el signo de las `x`, que es el mismo en entrenamiento y en la feria.

## Contenido del vector (v1.0)
1. **Pose** (22): `x, y` normalizados de nariz, ojos, orejas, hombros, codos y muñecas.
   Sin caderas: con encuadre de medio cuerpo suelen quedar fuera de cuadro (ver `docs/memes.md`).
2. **Ángulos** (7): codo izq/der, hombro izq/der (abertura del brazo), inclinación de los hombros,
   inclinación de la cabeza (roll) y giro aproximado de la cabeza (yaw).
3. **Distancias** (10): muñeca↔nariz, muñeca↔boca y muñeca↔hombro opuesto (izq/der), entre muñecas,
   inclinación vertical de la cabeza (pitch aprox.) y profundidad de cada muñeca respecto a los hombros (`z`).
4. **Relaciones** (0/1) (7): mano sobre la cabeza (izq/der), mano en la cara (izq/der), manos juntas,
   brazos cruzados y ambos brazos arriba.
5. **Manos** (11 por mano = 22): presencia, extensión de cada dedo (5, continua), normal de la palma
   (`y`, `z`), dirección del índice (`x`, `y`) y distancia punta del índice↔boca.
6. **Cara** (22): presencia más 21 blendshapes:
   `jawOpen`, `mouthSmileLeft/Right`, `mouthFrownLeft/Right`, `mouthPucker`, `mouthFunnel`,
   `mouthPressLeft/Right`, `eyeBlinkLeft/Right`, `eyeWideLeft/Right`, `eyeSquintLeft/Right`,
   `browInnerUp`, `browDownLeft/Right`, `browOuterUpLeft/Right`, `cheekPuff`.

Total v1.0: **90 features**. Los nombres exactos están en `FEATURE_NAMES` y en el snapshot.

## Criterios de aceptación
- `FEAT-01` Dados hombros en (0.4, 0.5) y (0.6, 0.5), después de normalizar el punto medio es (0, 0) y la distancia entre hombros es 1.
- `FEAT-02` **Invariancia a escala:** al escalar todos los landmarks ×2 alrededor de cualquier punto, el vector cambia menos de 1e-5.
- `FEAT-03` **Invariancia a traslación:** al desplazar todos los landmarks, el vector no cambia.
- `FEAT-04` Un codo en ángulo recto produce un ángulo de 90° ± 0.5°.
- `FEAT-05` Para cualquier `LandmarkResult` válido, `len(vector) == len(FEATURE_NAMES)` y no hay NaN ni infinitos.
- `FEAT-06` Si falta una mano (o la cara), su bloque se rellena con 0 y el flag de presencia vale 0, sin excepción.
- `FEAT-07` **Guarda de versión:** un test compara `FEATURE_NAMES` contra el snapshot `tests/fixtures/features/v<FEATURE_VERSION>.json`. Si cambian sin subir `FEATURE_VERSION` (y crear su snapshot), el test falla.
- `FEAT-08` Si no hay pose (`has_person` es `False`), se lanza `NoPersonError`.
- `FEAT-09` Una mano con solo el índice extendido tiene la extensión del índice claramente mayor que la del medio, el anular y el meñique.
- `FEAT-10` Con el índice sobre la boca, la distancia punta del índice↔boca es menor que 0.2 y "mano en la cara" vale 1.

## Casos borde
- Distancia entre hombros ≈ 0 (persona de perfil) → `NoPersonError`.
- Las coordenadas de MediaPipe están normalizadas por ancho y alto de la imagen: los ángulos dependen
  de la relación de aspecto. Se asume la misma cámara (4:3) en la recolección y en la feria.

## Fuera de alcance
Features temporales (velocidad, movimiento).

## Tareas
- [x] Constructor de `LandmarkResult` sintéticos para los tests (`tests/factories.py`)
- [x] TDD de FEAT-01…10
