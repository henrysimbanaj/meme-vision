# 003 — Extracción de características

- **Estado:** borrador
- **Owner:** Henry
- **Archivos:** `src/memevision/features.py`, `tests/test_features.py`

## Propósito
Transformar un `LandmarkResult` en un vector numérico de **longitud fija** que no dependa de
la distancia a la cámara ni de la posición o la altura de la persona.

## Contrato
```python
FEATURE_VERSION: str            # "1.0"; se sube en cualquier cambio de orden o de longitud
FEATURE_NAMES: tuple[str, ...]  # nombre de cada columna, en orden
def transform(lm: LandmarkResult) -> np.ndarray   # shape (len(FEATURE_NAMES),), float32, sin NaN
```

## Contenido del vector (v1.0, a confirmar tras analizar los memes)
1. Pose de la parte superior (nariz, ojos, orejas, hombros, codos, muñecas y caderas) en `(x, y)` normalizados.
2. Ángulos: codos, hombros, inclinación del torso, inclinación e yaw aproximado de la cabeza.
3. Distancias normalizadas: muñeca↔nariz, muñeca↔boca, muñeca↔hombro opuesto y entre las dos muñecas.
4. Relaciones: mano sobre la cabeza, mano en la cara, manos juntas, brazos cruzados.
5. Mano: apertura de cada mano (dedos extendidos) y un flag de presencia.
6. Blendshapes elegidos: `jawOpen`, `mouthSmileLeft/Right`, `mouthFrownLeft/Right`, `mouthPucker`,
   `eyeBlinkLeft/Right`, `eyeWideLeft/Right`, `browInnerUp`, `browDownLeft/Right`, `cheekPuff`.

## Criterios de aceptación
- `FEAT-01` Dados hombros en (0.4, 0.5) y (0.6, 0.5), después de normalizar el punto medio es (0, 0) y la distancia entre hombros es 1.
- `FEAT-02` **Invariancia a escala:** al escalar todos los landmarks ×2 alrededor de cualquier punto, el vector cambia menos de 1e-5.
- `FEAT-03` **Invariancia a traslación:** al desplazar todos los landmarks, el vector no cambia.
- `FEAT-04` Un codo en ángulo recto produce un ángulo de 90° ± 0.5°.
- `FEAT-05` Para cualquier `LandmarkResult` válido, `len(vector) == len(FEATURE_NAMES)` y no hay NaN ni infinitos.
- `FEAT-06` Si falta una mano, su bloque se rellena con 0 y el flag de presencia vale 0, sin excepción.
- `FEAT-07` **Guarda de versión:** un test compara `len(FEATURE_NAMES)` y un hash de los nombres contra un snapshot versionado. Si cambian sin subir `FEATURE_VERSION`, el test falla.
- `FEAT-08` Si no hay pose (`has_person` es `False`), se lanza `NoPersonError`.

## Casos borde
- Distancia entre hombros ≈ 0 (persona de perfil) → `NoPersonError`.

## Fuera de alcance
Features temporales (velocidad, movimiento).

## Tareas
- [ ] Constructor de `LandmarkResult` sintéticos para los tests (`tests/factories.py`)
- [ ] TDD de FEAT-01…08 en ese orden
