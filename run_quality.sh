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
  [ -n "$file" ] || continue
  [ -f "$file" ] || continue
  PY_FILES+=("$file")
done < <(
  {
    git diff --name-only -- '*.py'
    git diff --cached --name-only -- '*.py'
    git ls-files --others --exclude-standard -- '*.py'
  } | sort -u
)

if [ ${#PY_FILES[@]} -eq 0 ]; then
  echo "No changed Python files found."
  exit 0
fi

echo "Running black on ${#PY_FILES[@]} changed Python files..."
conda run -n agent_hub python -m black "${PY_FILES[@]}"

mkdir -p "$ROOT_DIR/.pylint.d"
echo "Running pylint on ${#PY_FILES[@]} changed Python files..."
PYTHONPATH="$ROOT_DIR" \
PYLINTHOME="$ROOT_DIR/.pylint.d" \
  conda run -n agent_hub python -m pylint "${PY_FILES[@]}"

echo "Quality checks completed."
