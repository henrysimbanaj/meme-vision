"""Pasa un meme del inbox al catálogo (spec 004).

Uso:
    python scripts/add_meme.py memes/inbox/michi-de-hecho.jpg --name "Michi De Hecho" \
        --caption "de hecho…" --trait "Índice arriba" --trait "Dientes de arriba"
"""

from __future__ import annotations

import argparse
from pathlib import Path

from memevision.catalog import add_meme


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("image", type=Path, help="imagen del inbox")
    parser.add_argument("--id", help="id del meme (por defecto, el nombre del archivo)")
    parser.add_argument("--name", required=True, help="nombre para la UI")
    parser.add_argument("--caption", default="", help="frase corta para la UI")
    parser.add_argument("--trait", action="append", default=[], help="cómo imitarlo (repetible)")
    args = parser.parse_args()

    spec = add_meme(
        args.image, args.id or args.image.stem, args.name, caption=args.caption, traits=args.trait
    )
    print(f"Agregado {spec.id} -> {spec.image_path}")
    print("Siguiente paso: recolectar sus datos con scripts/collect.py (spec 005).")


if __name__ == "__main__":
    main()
