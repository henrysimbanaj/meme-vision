#!/usr/bin/env bash
# Verificación única: la usan las personas, la IA, pre-commit y CI.
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== ruff check ==";  python -m ruff check .
echo "== ruff format ==";  python -m ruff format --check .
echo "== pytest ==";       python -m pytest -q "$@"
echo "OK: todo en verde"
