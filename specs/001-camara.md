# 001 — Cámara

- **Estado:** aprobada
- **Owner:** Henry
- **Archivos:** `src/memevision/camera.py`, `tests/test_camera.py`

## Propósito
Entregar frames BGR de forma uniforme, venga de una webcam, un video o una carpeta de imágenes.
Así el resto del sistema (y los tests) no dependen del hardware.

## Contrato
```python
class Camera:
    def __init__(self, source: int | str | Path = 0, mirror: bool = True): ...
    def get_frame(self) -> np.ndarray | None   # HxWx3 uint8 BGR, o None si no hay frame
    def release(self) -> None
    # es context manager: with Camera(0) as cam: ...
```

## Criterios de aceptación
- `CAM-01` Dada una carpeta con 3 imágenes, cuando llamo `get_frame()` 4 veces, entonces obtengo 3 arrays `uint8` de forma `(H, W, 3)` y luego `None`.
- `CAM-02` Dado un archivo de video, cuando lo leo hasta el final, entonces `get_frame()` devuelve `None` sin lanzar excepción.
- `CAM-03` Dado `mirror=True`, cuando leo una imagen asimétrica, entonces el frame está volteado horizontalmente.
- `CAM-04` Dada una webcam que se desconecta, cuando `get_frame()` falla, entonces devuelve `None`, e intenta reabrir la cámara como máximo 1 vez por segundo.
- `CAM-05` Dado `with Camera(...) as cam`, al salir del bloque se libera el recurso.

## Casos borde
- El índice de cámara no existe → `None` y un mensaje claro en el log, no un crash.
- En macOS, sin permiso de cámara → mensaje que explique cómo darlo.

## Fuera de alcance
Resolución configurable avanzada y múltiples cámaras.

## Tareas
- [ ] Tests CAM-01..03, CAM-05 con imágenes y videos generados en `tmp_path`
- [ ] CAM-04 con un `VideoCapture` falso (inyectable)
