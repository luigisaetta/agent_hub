#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

DOCKER_DEFAULT_PLATFORM=linux/amd64 docker build \
  -f "${REPO_ROOT}/demos/demo6/Dockerfile" \
  -t demo6-backend:1.0 \
  "${REPO_ROOT}"
