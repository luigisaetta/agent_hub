#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if ! command -v conda >/dev/null 2>&1; then
  echo "Error: conda is not installed or not in PATH."
  exit 1
fi

if ! conda run -n agent_hub python -m black --version >/dev/null 2>&1; then
  echo "Error: black is not available in conda environment 'agent_hub'."
  exit 1
fi

if ! conda run -n agent_hub python -m pylint --version >/dev/null 2>&1; then
  echo "Error: pylint is not available in conda environment 'agent_hub'."
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
conda run -n agent_hub python -m black "${PY_FILES[@]}"

echo "Running pylint on ${#PY_FILES[@]} Python files..."
conda run -n agent_hub python -m pylint "${PY_FILES[@]}"

echo "Quality checks completed."
