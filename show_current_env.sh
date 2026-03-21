#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
active_link="$SCRIPT_DIR/.env.active"

active_env_file=""
source_type=""

if [[ -n "${AGENT_HUB_ENV_FILE:-}" ]]; then
  active_env_file="$AGENT_HUB_ENV_FILE"
  source_type="AGENT_HUB_ENV_FILE"
elif [[ -e "$active_link" ]]; then
  active_env_file="$(cd "$SCRIPT_DIR" && pwd)/.env.active"
  source_type=".env.active"
fi

if [[ -z "$active_env_file" ]]; then
  echo "No active profile set."
  echo "Run: source ./set_env.sh <profile>"
  exit 1
fi

if [[ ! -f "$active_env_file" ]]; then
  echo "Active profile does not exist: $active_env_file"
  exit 1
fi

env_name="$(grep -E '^ENV_NAME=' "$active_env_file" | head -n1 | cut -d '=' -f2- || true)"
project_id="$(grep -E '^PROJECT_ID=' "$active_env_file" | head -n1 | cut -d '=' -f2- || true)"

echo "Current profile source: $source_type"
echo "Current env file: $active_env_file"
echo "ENV_NAME: ${env_name:-<not set>}"
echo "PROJECT_ID: ${project_id:-<not set>}"
echo "AGENT_HUB_REGION: ${AGENT_HUB_REGION:-<not set>}"
echo "AGENT_HUB_IS_PREPROD: ${AGENT_HUB_IS_PREPROD:-<not set>}"
