"""Evalúa el clasificador con personas no vistas (leave-one-person-out, spec 007).

Uso:
    python scripts/evaluate.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from memevision.config import DATA_RAW_DIR, ROOT
from memevision.dataset import load_dataset
from memevision.evaluation import ACCEPTANCE, evaluate_lopo, save_confusion_png

REPORTS_DIR = ROOT / "reports"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--trees", type=int, default=300, help="árboles del Random Forest")
    parser.add_argument("--data-dir", type=Path, default=DATA_RAW_DIR, help="carpeta del dataset")
    parser.add_argument("--out", type=Path, default=REPORTS_DIR, help="carpeta de reportes")
    args = parser.parse_args()

    df = load_dataset(args.data_dir)
    rep = evaluate_lopo(df, n_estimators=args.trees)

    print(f"Accuracy con personas no vistas (LOPO): {rep.accuracy:.1%}")
    verdict = "APROBADO" if rep.passed else "NO alcanza"
    print(f"Umbral del MVP {ACCEPTANCE:.0%}: {verdict}\n")
    print("Por persona:")
    for person, acc in rep.per_person.items():
        print(f"  {person}: {acc:.1%}")
    print("\nPor meme:              precisión  recall   F1   muestras")
    for label, m in rep.per_class.items():
        print(
            f"  {label:20s} {m['precision']:8.2f} {m['recall']:7.2f} {m['f1-score']:5.2f} "
            f"{int(m['support']):8d}"
        )
    if rep.top_confusions():
        print("\nLo que más se confunde (real -> predicho):")
        for real, pred, n in rep.top_confusions():
            print(f"  {real} -> {pred}: {n}")

    args.out.mkdir(parents=True, exist_ok=True)
    save_confusion_png(rep, args.out / "confusion_matrix.png")
    json_text = json.dumps(rep.to_dict(), indent=2, ensure_ascii=False) + "\n"
    (args.out / "evaluation.json").write_text(json_text, encoding="utf-8")
    print(f"\nGuardado: {args.out / 'confusion_matrix.png'} y evaluation.json")


if __name__ == "__main__":
    main()
