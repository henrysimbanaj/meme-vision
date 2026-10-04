# Meme Vision 🐱

Imita un meme de michi de TikTok frente a la cámara y la computadora adivina cuál es.
Proyecto para la casa abierta. Funciona en Kubuntu y en macOS (Apple Silicon).

## Instalación (Python ≥ 3.11; probado con 3.14)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
python scripts/download_models.py     # modelo de MediaPipe (13 MB, va a models/)
bash scripts/check.sh                 # debe terminar en "OK"
```

> **macOS:** la primera vez, da permiso de cámara a la Terminal o al IDE
> (Ajustes → Privacidad y seguridad → Cámara).

## Uso

```bash
python scripts/demo.py                             # la app de la feria (sin modelo: modo en vivo)

# 1. Recolectar datos: cada persona imita cada meme (y "neutral"), 2 sesiones de 20 s
python scripts/collect.py michi-fuerza --person P01
python scripts/collect.py neutral --person P01

# 2. Entrenar y evaluar con personas no vistas (se necesitan al menos 2 personas)
python scripts/train.py
python scripts/evaluate.py                         # reports/confusion_matrix.png

# Agregar un meme nuevo desde memes/inbox/
python scripts/add_meme.py memes/inbox/michi-tos.jpg --name "Michi Tos" --trait "Boca en O"
```

En la demo: `m` cambia de modo (reto, libre, en vivo), `espacio` inicia una nueva ronda,
`f` activa la pantalla completa y `q` sale. No se guardan fotos ni videos.

## Cómo se trabaja

- **SDD:** cada módulo tiene su spec en `specs/`. Primero la spec, después el código.
- **TDD:** cada criterio de aceptación (`FEAT-01`, …) es un test que se escribe antes que el código.
- **Harness:** `AGENTS.md` fija las reglas para cualquier IA; `scripts/check.sh`, pre-commit y CI las hacen cumplir.
- **Memes:** las imágenes candidatas van en `memes/inbox/` y las elegidas en `memes/catalog/`.

Documentación: `docs/` (guía técnica, colaboración y decisiones en `docs/decisions/`).
