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

## Uso (a medida que se implementen los módulos)

```bash
python scripts/collect.py <meme_id> --person P01   # recolectar datos
python scripts/train.py                            # entrenar
python scripts/evaluate.py                         # métricas + matriz de confusión
python scripts/demo.py                             # la app de la feria
```

## Cómo se trabaja

- **SDD:** cada módulo tiene su spec en `specs/`. Primero la spec, después el código.
- **TDD:** cada criterio de aceptación (`FEAT-01`, …) es un test que se escribe antes que el código.
- **Harness:** `AGENTS.md` fija las reglas para cualquier IA; `scripts/check.sh`, pre-commit y CI las hacen cumplir.
- **Memes:** las imágenes candidatas van en `memes/inbox/` y las elegidas en `memes/catalog/`.

Documentación: `docs/` (guía técnica, colaboración y decisiones en `docs/decisions/`).
