#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://127.0.0.1:8000/chat/stream}"
USER_REQUEST="${USER_REQUEST:-}"
if [[ -z "$USER_REQUEST" ]]; then
  USER_REQUEST="Spiegami cosa è l'aspirina"
fi

MODEL_ID="${MODEL_ID:-openai.gpt-5.4}"
RERANKER_MODEL_ID="${RERANKER_MODEL_ID:-openai.gpt-5.4}"
TOP_K="${TOP_K:-10}"
TOP_N="${TOP_N:-8}"

json_escape() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  value="${value//$'\n'/\\n}"
  value="${value//$'\r'/\\r}"
  value="${value//$'\t'/\\t}"
  printf '%s' "$value"
}

ESCAPED_USER_REQUEST="$(json_escape "$USER_REQUEST")"
ESCAPED_MODEL_ID="$(json_escape "$MODEL_ID")"
ESCAPED_RERANKER_MODEL_ID="$(json_escape "$RERANKER_MODEL_ID")"

curl -N -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d "{
    \"user_request\":\"$ESCAPED_USER_REQUEST\",
    \"history\":[],
    \"model_id\":\"$ESCAPED_MODEL_ID\",
    \"reranker_model_id\":\"$ESCAPED_RERANKER_MODEL_ID\",
    \"top_k\":$TOP_K,
    \"top_n\":$TOP_N
  }"
