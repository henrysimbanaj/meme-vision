"""Descarga los modelos .task de MediaPipe a models/ (spec 002).

Uso: python scripts/download_models.py
"""

from __future__ import annotations

import urllib.request

from memevision.config import MODELS_DIR, ROOT
from memevision.landmarks import MODEL_URLS


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    for name, url in MODEL_URLS.items():
        target = MODELS_DIR / name
        if target.exists():
            print(f"ya existe: {target.relative_to(ROOT)}")
            continue
        print(f"descargando {name} ...")
        partial = target.with_suffix(".part")
        urllib.request.urlretrieve(url, partial)
        partial.replace(target)
        print(f"listo: {target.relative_to(ROOT)} ({target.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
