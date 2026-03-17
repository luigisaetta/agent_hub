#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if ! command -v black >/dev/null 2>&1; then
  echo "Error: black is not installed or not in PATH."
  exit 1
fi

if ! command -v pylint >/dev/null 2>&1; then
  echo "Error: pylint is not installed or not in PATH."
  exit 1
fi

PY_FILES=()
while IFS= read -r file; do
  PY_FILES+=("$file")
done < <(
  find . -type f -name "*.py" \
    -not -path "./.git/*" \
    -not -path "*/__pycache__/*" \
    | sort
)

if [ ${#PY_FILES[@]} -eq 0 ]; then
  echo "No Python files found."
  exit 0
fi

echo "Running black on ${#PY_FILES[@]} Python files..."
black "${PY_FILES[@]}"

echo "Running pylint on ${#PY_FILES[@]} Python files..."
pylint "${PY_FILES[@]}"

echo "Quality checks completed."
