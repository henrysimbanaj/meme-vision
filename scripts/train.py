"""Entrena el clasificador con el dataset de data/raw/ (spec 006).

Uso:
    python scripts/train.py                      # aparta la última persona para medir
    python scripts/train.py --test-person P02    # elige a quién apartar (repetible)
"""

from __future__ import annotations

import argparse
from pathlib import Path

from memevision.classifier import MODEL_DIR, MemeClassifier, default_test_persons, split_by_person
from memevision.config import DATA_RAW_DIR
from memevision.dataset import load_dataset
from memevision.features import FEATURE_NAMES


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--test-person", action="append", help="persona no vista (repetible)")
    parser.add_argument("--trees", type=int, default=300, help="árboles del Random Forest")
    parser.add_argument("--data-dir", type=Path, default=DATA_RAW_DIR, help="carpeta del dataset")
    parser.add_argument("--model-dir", type=Path, default=MODEL_DIR, help="dónde guardar el modelo")
    args = parser.parse_args()

    df = load_dataset(args.data_dir)
    print(f"Dataset: {len(df)} muestras, {df['person'].nunique()} personas")
    print(df.groupby(["label", "person"]).size().unstack(fill_value=0).to_string(), "\n")

    test_persons = args.test_person or default_test_persons(df)
    accuracy = None
    if test_persons:
        train, test = split_by_person(df, test_persons)
        missing = set(df["label"]) - set(train["label"])
        if missing:
            print(f"Aviso: sin muestras de train para {sorted(missing)}")
        clf = MemeClassifier.fit(train, n_estimators=args.trees)
        predicted = clf.predict_batch(test[list(FEATURE_NAMES)].to_numpy())
        accuracy = float((predicted == test["label"].to_numpy()).mean())
        print(f"Precisión con personas no vistas {test_persons}: {accuracy:.1%}", end=" ")
        print(f"({len(test)} muestras)")
    else:
        print("Aviso: hay una sola persona; no se puede medir con alguien no visto.")

    final = MemeClassifier.fit(df, n_estimators=args.trees)
    final.card.update(
        persons_test=list(test_persons),
        samples_test=int(df["person"].isin(test_persons).sum()),
        accuracy_unseen_person=accuracy,
    )
    final.save(args.model_dir)
    print(f"Modelo final (todas las personas) guardado en {args.model_dir}")
    print("Detalle por clase y matriz de confusión: python scripts/evaluate.py")


if __name__ == "__main__":
    main()
