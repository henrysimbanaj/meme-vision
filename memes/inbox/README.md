# memes/inbox — deja aquí las imágenes de michis

Pon aquí **todas** las imágenes candidatas de memes de michis de TikTok, sin preocuparte todavía por cuáles se usarán.

## Cómo nombrarlas
- `nombre-del-meme.jpg`, en minúsculas, con guiones y sin espacios. Ejemplos: `gato-sorprendido.jpg`, `michi-llorando.png`.
- Si hay varias versiones del mismo meme: `gato-sorprendido-2.jpg`.

## Formatos
`.jpg`, `.jpeg`, `.png` o `.webp`, idealmente de menos de 800 KB (pre-commit bloquea archivos más grandes).
Sirven capturas de TikTok, pero conviene recortar la interfaz de la app.

## Opcional: contexto
Si el meme tiene una frase o un audio conocido, créale un `.txt` con el mismo nombre (`gato-sorprendido.txt`) con
la frase y lo que significa. Ayuda a escribir su spec y los textos de la UI.

## Qué pasa después
1. Se analiza cada imagen y en `docs/memes.md` se propone cómo lo imitaría un humano (pose, manos, expresión).
2. Se eligen los 3–5 más **distinguibles entre sí**.
3. Los elegidos pasan a `memes/catalog/<id>/` con `reference.png` + `meme.yaml` (spec 004).
