#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

usage() {
  echo "Usage: source ./set_env.sh <profile>"
  echo "Available profiles: preprod-chicago, preprod-frankfurt, prod-frankfurt"
}

if [[ $# -ne 1 ]]; then
  usage
  return 1 2>/dev/null || exit 1
fi

profile="$1"

case "$profile" in
  preprod-chicago)
    env_file=".env.preprod-chicago"
    ;;
  preprod-frankfurt)
    env_file=".env.preprod-frankfurt"
    ;;
  prod-frankfurt)
    env_file=".env.prod-frankfurt"
    ;;
  *)
    echo "Unknown profile: $profile"
    usage
    return 1 2>/dev/null || exit 1
    ;;
esac

target="$SCRIPT_DIR/$env_file"
active_link="$SCRIPT_DIR/.env.active"

if [[ ! -f "$target" ]]; then
  echo "Profile file not found: $target"
  return 1 2>/dev/null || exit 1
fi

ln -sfn "$target" "$active_link"
echo "Active profile set: $profile"
echo ".env.active -> $env_file"

if (return 0 2>/dev/null); then
  export AGENT_HUB_ENV_FILE="$target"
  echo "Exported AGENT_HUB_ENV_FILE=$AGENT_HUB_ENV_FILE"
else
  echo "Tip: run 'source ./set_env.sh $profile' to export AGENT_HUB_ENV_FILE in current shell."
fi
