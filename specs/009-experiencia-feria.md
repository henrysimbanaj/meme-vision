# 009 — Experiencia de feria

- **Estado:** implementada (MVP)
- **Owner:** Compañera (implementado por Henry para el MVP; revisa la compañera)
- **Archivos:** `src/memevision/game.py`, `src/memevision/ui.py`, `scripts/demo.py`,
  `tests/test_game.py`, `tests/test_ui.py`

## Propósito
La app de la casa abierta: divertida, rápida y clara para visitantes de colegio. Sin pantallas técnicas.

## Modos
- **Reto** (`challenge`, por defecto): el sistema elige un meme al azar y la persona lo imita.
- **Libre** (`free`): la persona imita cualquiera; el sistema adivina cuál.
- **En vivo** (`live`): muestra el esqueleto y las 3 predicciones más probables en tiempo real.
  Sirve para explicar cómo funciona. Es el único modo disponible si todavía no hay modelo entrenado.

## Estados (modos reto y libre)
```text
BUSCANDO --persona visible--> DETECTADA --1 s--> CUENTA (3, 2, 1) --> ANALIZANDO
    ^                                                                     |
    |                                   estable (spec 008) o 4 s máximo    v
    +------------------------- 5 s ---------------------------------- RESULTADO
```
- Si la persona desaparece más de 1.5 s en DETECTADA, CUENTA o ANALIZANDO → BUSCANDO.
- En RESULTADO: el meme con su porcentaje. En modo reto, además, si superó el reto o no.
- Al terminar RESULTADO empieza una ronda nueva con otro meme objetivo (distinto al anterior).

## Contrato
```python
class Phase(StrEnum): SEARCHING, DETECTED, COUNTDOWN, ANALYZING, RESULT, LIVE
class Mode(StrEnum): CHALLENGE, FREE, LIVE
@dataclass(frozen=True)
class GameState:
    mode: Mode; phase: Phase; round: int; target: str | None
    remaining_s: float; live: Prediction | None; result: Prediction | None; success: bool | None
class Game:
    def __init__(self, meme_ids: Sequence[str], mode=Mode.CHALLENGE, rng=random.Random(),
                 clock=time.monotonic, timings: Timings = Timings()): ...
    def update(self, person_visible: bool, prediction: Prediction | None, stable: bool) -> GameState
    def set_mode(self, mode: Mode) -> GameState
    def next_round(self) -> GameState
def render(frame, state: GameState, catalog: dict[str, MemeSpec], landmarks, banner="") -> np.ndarray
```
`render` devuelve un lienzo de 1280x720 BGR.

## Criterios de aceptación
- `UX-01` Sin persona, el juego queda en BUSCANDO.
- `UX-02` Con persona visible pasa a DETECTADA y, tras 1 s, a CUENTA.
- `UX-03` La CUENTA dura 3 s y luego pasa a ANALIZANDO.
- `UX-04` En ANALIZANDO, una predicción estable pasa a RESULTADO con esa predicción. Si en 4 s no hay una estable, el resultado es la última predicción (o `no_seguro` si no hubo ninguna).
- `UX-05` En modo reto, `success` es `True` solo si el meme del resultado es el objetivo. En modo libre es `None`.
- `UX-06` RESULTADO dura 5 s y luego empieza una ronda nueva, con un objetivo distinto del anterior (si hay 2 o más memes).
- `UX-07` Si la persona desaparece más de 1.5 s durante DETECTADA, CUENTA o ANALIZANDO, se vuelve a BUSCANDO.
- `UX-08` Cambiar de modo reinicia la ronda. En modo en vivo la fase es siempre `LIVE` y `live` lleva la predicción actual.
- `UX-09` El objetivo del reto nunca es `neutral`.
- `UX-10` `render` devuelve un lienzo 1280x720 en todas las fases y modos, con o sin landmarks y resultado.

## Controles (teclado)
`q`/`Esc` salir · `m` cambiar de modo · `espacio` nueva ronda · `f` pantalla completa.

## Casos borde
- Sin modelo entrenado → la demo arranca en modo en vivo, con un aviso para entrenar.
- Resultado `neutral` → "No estás imitando ningún meme".

## Fuera de alcance
Sonidos, animaciones complejas y ranking de puntajes (después del MVP).

## Tareas
- [x] `game.py` + tests UX-01..09 con reloj falso
- [x] `ui.py` + test UX-10
- [x] `scripts/demo.py`
- [ ] Probar con visitantes reales y ajustar tiempos y textos
