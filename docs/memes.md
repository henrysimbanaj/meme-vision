# Memes — análisis y selección

Estado: **selección inicial hecha** (4 memes, ya en `memes/catalog/`). Las frases marcadas con (¿?) aún están por confirmar.

Cómo leer este documento:
- Lo que dice **(¿?)** es una suposición sobre la frase o el significado del meme: corrígelo.
- Los emojis pegados en las imágenes (👊, ☝️, 🤫, 🤙…) se imitan con la **mano real**, que es lo que ve MediaPipe.
- Los accesorios (sombrero, bigote, lentes, ruedita de carga) **no se detectan**: no cuentan como rasgo.
- Dificultad = qué tan fácil es que el modelo lo separe de los demás y de `neutral` (no qué tan difícil es imitarlo).

## Resumen

| id | Imagen | Cómo lo imita un humano | Rasgos distintivos (features) | Dificultad | ¿Elegido? |
|---|---|---|---|---|---|
| `michi-fuerza` | Gato gris con los dos brazos flexionados arriba | Los dos brazos arriba, codos a la altura de los hombros, puños cerrados (pose de "músculo") | Muñecas sobre los hombros, codos ~90°, simetría | Baja | Sí (inicial) |
| `michi-silencio` | Gato blanco, 🤫 dedo índice en los labios | Índice vertical sobre los labios, ojos bien abiertos, mirando a la cámara | Punta del índice ↔ boca muy cerca, solo índice extendido | Baja | Sí (inicial) |
| `michi-67` | Gato blanco sonriendo de lado, un ojo entrecerrado, manos con palmas arriba ("6 7") | Las dos manos al frente a la altura del pecho, palmas arriba, sonrisa de lado y un ojo medio cerrado | Dos manos abiertas bajo los hombros y cerca del torso, sonrisa, parpadeo asimétrico | Media | Sí (inicial) |
| `michi-burla` | Gato blanco con la boca muy abierta y una mano señalando | Señalar a la cámara con el índice y reírse con la boca muy abierta | `jawOpen` alto + un brazo extendido al frente con el índice | Media | Sí (inicial) |
| `michi-tos` | Gato blanco tosiendo: boca en "O", lengua afuera, cabeza ladeada | Boca abierta redonda, cabeza inclinada hacia un lado, ojos bien abiertos, manos abajo | `jawOpen` + `mouthFunnel`, inclinación de la cabeza, sin brazos | Media | Después |
| `michi-de-hecho` | Gato con lentes, dientes afuera y ☝️ ("de hecho…" 🤓) | Índice arriba al lado de la cara, mostrar los dientes de arriba mordiendo el labio | Mano a la altura de la cabeza, solo índice extendido, boca | Media | Después |
| `michi-tirando-flow` | Gatito bailando parado, las dos patas juntas frente a la boca, explosión detrás | Las dos manos (puños) juntas frente a la boca/nariz, un poco agachado, "bailando" | Las dos muñecas cerca de la cara y juntas | Media | Después |
| `michi-golpe` | Gato naranja lanzando un puñetazo (👊) hacia la cámara | Un puño extendido hacia la cámara | Brazo extendido al frente y puño cerrado. La profundidad (z) es poco fiable en 2D | Alta | No |
| `michi-saca-plan` | Gato gris sorprendido con la lengua afuera y 🤙 en el pecho. Frase: (¿?) | Mano 🤙 (pulgar y meñique) frente al pecho, boca abierta, ojos muy abiertos | Forma de la mano 🤙, `jawOpen`, `eyeWide`. La lengua no es un blendshape de MediaPipe | Alta | No |
| `michi-panas` | Dos gatitos dándose la mano 🤝 | Requiere dos personas (o darse la mano a uno mismo) | Manos juntas al frente. El sistema sigue a **una** persona (spec 002) | Alta | No |

## Selección inicial (4 + `neutral`)

Criterio: que cada meme se reconozca por **un rasgo fuerte distinto** y que haya variedad entre brazos, manos y cara.

| Meme | Rasgo principal que lo separa |
|---|---|
| `michi-fuerza` | Los dos brazos arriba (el único con muñecas sobre los hombros) |
| `michi-silencio` | Una mano en la boca con el índice |
| `michi-67` | Las dos manos al frente con las palmas arriba, pegadas al torso |
| `michi-burla` | Brazo extendido señalando + boca muy abierta |

Candidatos para ampliar después, por orden: `michi-tos` (solo cara, pero choca con la boca abierta de `michi-burla`),
`michi-de-hecho` (choca un poco con `michi-silencio`) y `michi-tirando-flow` (choca con `michi-silencio`).

## Encuadre y descripciones

Las descripciones de este documento son un punto de partida: se ajustan cuando se prueben con la cámara real.
- **Encuadre supuesto:** medio cuerpo (de la cabeza a la cintura), con los codos y las manos dentro del cuadro.
  Si la cámara solo ve la cara, `michi-fuerza` y `michi-burla` dejan de funcionar.
- **Cuándo se congelan:** justo antes de recolectar datos (spec 005). Cambiar la pose de un meme
  después obliga a volver a grabarlo.

## Matriz de distinguibilidad

✔ = rasgo presente · ~ = parcial · vacío = ausente

| Meme | Brazos arriba | 1 mano en la cara | 2 manos en la cara | Brazo al frente | Palmas arriba | Solo índice | Boca muy abierta | Ojos cerrados | Sonrisa | Cabeza ladeada | Ceja asimétrica |
|---|---|---|---|---|---|---|---|---|---|---|---|
| michi-fuerza | ✔ | | | | | | | | | | |
| michi-silencio | | ✔ | | | | ✔ | | | | | |
| michi-67 | | | | ~ | ✔ | | | ~ | ✔ | | ~ |
| michi-burla | | | | ✔ | | ✔ | ✔ | | | | |
| michi-tos | | | | | | | ✔ | | | ✔ | |
| michi-de-hecho | | ~ | | | | ✔ | | | | | |
| michi-tirando-flow | | | ✔ | | | | | | | | |
| michi-golpe | | | | ✔ | | | | | | | |
| michi-saca-plan | | | | | | | ✔ | | | | |

## Impacto en la spec 003 (features)

Si se eligen los 4 propuestos, al vector v1.0 le faltan:
- **Forma de la mano por dedo**, no solo la apertura: saber si solo el índice está extendido (`michi-silencio`, `michi-burla`).
- **Distancia de la punta del índice a la boca**, además de muñeca↔boca.
- **Orientación de la palma** (arriba o abajo) para `michi-67`.
- Si entra `michi-tos`: el blendshape `mouthFunnel`.

## Decisiones pendientes (para Henry y la compañera)

- [x] Se aceptan memes que no son de michis (Henry, 2026-09-29).
- [ ] Corregir las frases y significados marcados con (¿?).
- [x] Selección inicial: los 5 más fáciles de distinguir (Henry, 2026-09-29).
- [x] Pasar esos memes a `memes/catalog/<id>/` (spec 004).

## Clase `neutral`
La persona está parada, con los brazos abajo y la cara relajada, sin imitar nada. Se entrena para que
el sistema no fuerce un meme. Conviene incluir variantes "casi meme" (rascarse la cara, cruzar los brazos,
sonreír) para que el modelo aprenda a decir "No estoy seguro".
