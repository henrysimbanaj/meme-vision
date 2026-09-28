# ADR-001 — Random Forest como modelo inicial

- **Estado:** aceptada
- **Fecha:** 2026-09-28

## Contexto
El dataset es tabular (features de landmarks), pequeño (miles de filas) y no hay GPU garantizada.

## Decisión
Usar `RandomForestClassifier(n_estimators=300, random_state=42)` como base.

## Motivo
Se entrena en segundos, da probabilidades, es explicable en la feria y no necesita mucho ajuste.
Otros modelos (k-NN, SVM, MLP) solo se comparan si queda tiempo después de M3.
