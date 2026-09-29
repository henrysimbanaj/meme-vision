# ADR-002 — MediaPipe 1.x con Tasks API

- **Estado:** aceptada (Kubuntu) · pendiente de confirmar en la Mac M2
- **Fecha:** 2026-09-28

## Contexto
El Python del sistema en el Kubuntu de Henry es 3.14. Hacía falta saber si MediaPipe funciona ahí y qué API usar.

## Resultado del spike (Kubuntu, 2026-09-28)
- `mediapipe 1.0.1` se publica como wheel `py3-none` (x86_64, macOS arm64, …): **no hace falta instalar Python 3.12**.
- Se instaló en un venv con Python 3.14.4, junto con opencv 5.0.0, numpy 2.5.3 y scikit-learn 1.9.1.
- `mediapipe.solutions` **ya no existe** en 1.x. Están disponibles `PoseLandmarker`, `HandLandmarker`, `FaceLandmarker` y `HolisticLandmarker`.
- MediaPipe depende de `opencv-contrib-python`, así que **no se debe instalar `opencv-python` a la vez**.

## Decisión
- Python ≥ 3.11. CI prueba 3.12 y 3.14 en Ubuntu y macOS-14.
- Usar la Tasks API con **`HolisticLandmarker`** (decidido el 2026-09-29) en lugar de Pose + Hand + Face por separado:
  - un solo modelo `.task` (13 MB) y una sola llamada por frame (~31 ms en Kubuntu, CPU);
  - asigna cada mano al cuerpo, así que izquierda/derecha es la de la persona sin heurísticas propias;
  - entrega los 52 blendshapes con `output_face_blendshapes=True`.
  - Contra: sigue a una sola persona. Para la feria es lo que se quiere.

## Pendiente
- [ ] En la Mac M2: `pip install -e ".[dev]"` + `bash scripts/check.sh`, y anotar aquí el resultado.
