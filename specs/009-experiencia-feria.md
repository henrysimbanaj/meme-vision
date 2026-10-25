# 009 — Experiencia de feria

- **Estado:** implementada (MVP)
- **Owner:** Compañera (implementado por Henry para el MVP; revisa la compañera)
- **Archivos:** `src/memevision/game.py`, `src/memevision/ui.py`, `scripts/demo.py`,
  `tests/test_game.py`, `tests/test_ui.py`

## Propósito
La app de la casa abierta: divertida, rápida y clara para visitantes de colegio. Sin pantallas técnicas.
El nombre del juego en la pantalla de inicio es **Live WebCat**.

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
- En RESULTADO, modo reto: un mensaje según los puntos de la ronda (0–100).
  80 o más: «Excelente». 55–79: «Buen Trabajo». 30–54: «Casi». Menos de 30: «¡Sigue intentando!».
  Debajo, los puntos de este michi y el total en bloques separados y legibles.
- Al terminar RESULTADO empieza una ronda nueva con otro meme objetivo (distinto al anterior),
  hasta completar **10 rondas**. Luego pasa a RESUMEN: puntaje total, leaderboard y
  el botón «Volver a intentar».
- Al abrir la app, y al pulsar «Volver a intentar», se muestra un menú arcade animado con el logo
  de Live WebCat, un botón «Jugar» redondeado y seis memes de gato del catálogo. La cámara y el
  detector de pose no se abren mientras el menú está visible. «Jugar» (clic, Enter o espacio)
  empieza una partida nueva.
- Durante la partida suena `assets/audio/musictheme.mp3` en bucle. Al terminar el resultado de la
  ronda 10, la música de fondo se detiene y suena una vez `assets/audio/fnafcelebracion.mp3`.
  Al regresar al inicio para volver a jugar, vuelve a sonar la música de fondo.
- En modo reto, cada ronda suma el parecido con el meme de la pantalla: la probabilidad
  de ese meme, de 0 a 100 puntos. Se acumula durante las 10 rondas.
- En RESUMEN se puede escribir un nombre y guardarlo con Enter. El nombre es opcional
  y queda solo en `data/leaderboard.json` (no va a git). El resumen permanece visible hasta que
  el participante elija volver al menú o salir; la duración del audio no limita el tiempo disponible.

## Contrato
```python
class Phase(StrEnum): SEARCHING, DETECTED, COUNTDOWN, ANALYZING, RESULT, LIVE, SUMMARY
class Mode(StrEnum): CHALLENGE, FREE, LIVE
@dataclass(frozen=True)
class GameState:
    mode: Mode; phase: Phase; round: int; target: str | None
    remaining_s: float; live: Prediction | None; result: Prediction | None; success: bool | None
    score: int = 0; round_points: int = 0
class Game:
    def __init__(self, meme_ids: Sequence[str], mode=Mode.CHALLENGE, rng=random.Random(),
                 clock=time.monotonic, timings: Timings = Timings()): ...
    def update(self, person_visible: bool, prediction: Prediction | None, stable: bool) -> GameState
    def set_mode(self, mode: Mode) -> GameState
    def next_round(self) -> GameState
def render(frame, state: GameState, catalog: dict[str, MemeSpec], landmarks, banner="", time_s=None) -> np.ndarray
def render_start(catalog=None, time_s=None) -> np.ndarray
def button_at(x: int, y: int) -> str | None   # "start" o "retry"
```
`render` y `render_start` devuelven un lienzo de 1280x720 BGR.

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
- `UX-11` En modo reto, los puntos de la ronda son la probabilidad del meme objetivo × 100, y se suman al total.
- `UX-12` Tras 10 rondas (configurable en tests), RESULTADO pasa a RESUMEN con el puntaje acumulado y no abre la ronda 11.
- `UX-13` `play_again` vuelve a la ronda 1 con puntaje 0.
- `UX-14` Guardar un nombre y un puntaje los agrega al leaderboard, ordenado de mayor a menor. Un nombre vacío no se guarda.
- `UX-15` `render_start` devuelve un lienzo 1280x720. El clic en «Jugar» lo identifica `button_at` como `start`; fuera del botón no hay acción.
- `UX-16` El mensaje del resultado depende de los puntos: 80+ «Excelente», 55–79 «Buen Trabajo», 30–54 «Casi», menos de 30 «¡Sigue intentando!».
- `UX-17` La música de fondo suena durante el juego y se detiene al salir de la partida.
- `UX-18` Al entrar a RESUMEN al terminar las 10 rondas, se reproduce una vez el tema de celebración.
- `UX-23` RESUMEN permanece visible y acepta el nombre hasta que el participante elija «Volver a
  intentar» o salir. Que termine el tema de celebración no abandona ni cambia la pantalla.
- `UX-24` El fondo de las pantallas de partida y resumen tiene burbujas animadas en una paleta
  oceánica azul petróleo, azul bruma y coral suave; no dibuja líneas horizontales. El mismo gato
  pixelado del menú aparece como mascota animada en la partida y el resumen.
- `UX-25` Al activar pantalla completa, el lienzo se adapta al área visible real manteniendo su
  proporción y centrado; los clics del menú y resumen siguen correspondiendo a sus coordenadas.
- `UX-19` El menú inicial muestra el logo de Live WebCat en lugar del título de texto, seis tarjetas
  con memes del catálogo y un botón Jugar redondeado; el personaje gato y el fondo tienen animación
  tipo videojuego.
- `UX-20` Durante el análisis en modo reto, la barra del meme objetivo permanece visible y su color
  cambia de rojo a amarillo y a verde según su probabilidad, con transición continua y verde al 100%;
  no muestra la etiqueta «OBJETIVO» y presenta el porcentaje exacto, grande y destacado, en el mismo
  color de la barra. La interfaz no muestra la leyenda de atajos de teclado en el pie.
- `UX-21` Antes de la cuenta regresiva aparece «¿Listo?» y durante ella «¡Imita al gato!» con
  animación estilo videojuego y texto en cian o menta, sin morado ni amarillo.
- `UX-22` Durante ANALIZANDO no aparecen rótulos de estado sobre la cámara ni en el pie; la
  cámara muestra una señal animada visual. En resultados de reto, el mensaje es destacado y
  alentador, y «PUNTOS DE ESTE MICHI» y «PUNTAJE TOTAL» se leen como dos tarjetas separadas.

## Controles (teclado)
`q`/`Esc` salir · `m` cambiar de modo · `espacio` nueva ronda · `f` pantalla completa.
Los atajos siguen disponibles, pero no aparecen como leyenda en la interfaz.

## Casos borde
- Sin modelo entrenado → la demo arranca en modo en vivo, con un aviso para entrenar.
- Resultado `neutral` → "No estás imitando ningún meme".

## Fuera de alcance
Animaciones complejas durante las rondas.

## Tareas
- [x] `game.py` + tests UX-01..09 con reloj falso
- [x] `ui.py` + test UX-10
- [x] Pantalla de inicio Live WebCat (UX-15); «Volver a intentar» vuelve a ella y suelta la cámara
- [x] `scripts/demo.py`
- [ ] Probar con visitantes reales y ajustar tiempos y textos
