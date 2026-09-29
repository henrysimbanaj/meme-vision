# ADR-003 — Vector de features v1.0

- **Estado:** aceptada
- **Fecha:** 2026-09-29

## Contexto
La spec 003 proponía un vector base. Al analizar los memes elegidos (`docs/memes.md`) faltaban
rasgos para separar `michi-silencio`, `michi-burla` y `michi-67`.

## Decisión
Vector v1.0 de 90 features (detalle en la spec 003):
- **Sin caderas:** con encuadre de medio cuerpo suelen estar fuera de cuadro y MediaPipe las inventa.
- **Forma de la mano por dedo** (extensión continua de los 5 dedos), **normal de la palma** y
  **dirección del índice**: separan "solo índice" (silencio, burla) y "palmas arriba" (67).
- **Distancia punta del índice↔boca:** el rasgo principal de `michi-silencio`.
- **Profundidad `z` de las muñecas:** ayuda con "brazo hacia la cámara" (`michi-burla`), aunque es ruidosa.
- **21 blendshapes** en lugar de 15: se agregan `mouthFunnel`, `mouthPress*`, `eyeSquint*` y
  `browOuterUp*` para poder sumar memes después (`michi-tos`, `michi-ceja`) sin cambiar la versión.
- Ángulos en **radianes**, para que la tolerancia de 1e-5 de FEAT-02 se cumpla con float32.

## Consecuencias
Cualquier cambio de orden o de longitud sube `FEATURE_VERSION`, crea
`tests/fixtures/features/v<versión>.json` y obliga a volver a recolectar o recalcular el dataset.
