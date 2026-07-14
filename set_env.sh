#!/usr/bin/env zsh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

usage() {
  echo "Usage: source ./set_env.sh <profile>"
  echo "Available profiles: prod-chicago, prod-frankfurt, prod-london"
}

if [[ $# -ne 1 ]]; then
  usage
  echo "Missing profile argument."
  return 1 2>/dev/null || exit 1
fi

profile="$1"

case "$profile" in
  prod-chicago)
    env_file=".env.prod-chicago"
    region="us-chicago-1"
    ;;
  prod-frankfurt)
    env_file=".env.prod-frankfurt"
    region="eu-frankfurt-1"
    ;;
  prod-london)
    env_file=".env.prod-london"
    region="uk-london-1"
    ;;
  *)
    echo "Unknown profile: $profile"
    usage
    echo "Profile not recognized."
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
  export AGENT_HUB_REGION="$region"
  echo "Exported AGENT_HUB_ENV_FILE=$AGENT_HUB_ENV_FILE"
  echo "Exported AGENT_HUB_REGION=$AGENT_HUB_REGION"
else
  echo "Tip: run 'source ./set_env.sh $profile' to export AGENT_HUB_* vars in current shell."
fi
