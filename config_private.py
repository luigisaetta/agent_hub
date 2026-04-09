"""
Author: L. Saetta
Last modified: 2026-03-21
License: MIT

Description:
    Private configuration module: load secrets from env vars.

    DO NOT MAKE CHANGES HERE. Secrets are defined in .env files (see README)
"""

from pathlib import Path
import os

from dotenv import load_dotenv

from config import REGION

ROOT_DIR = Path(__file__).resolve().parent


def _default_profile_file() -> str:
    if REGION == "us-chicago-1":
        return ".env.prod-chicago"
    if REGION == "eu-frankfurt-1":
        return ".env.prod-frankfurt"

    raise NotImplementedError(f"No default secret profile for REGION={REGION!r}")


def _resolve_env_file() -> Path:
    explicit = os.getenv("AGENT_HUB_ENV_FILE")
    if explicit:
        env_path = Path(explicit).expanduser()
        if not env_path.is_absolute():
            env_path = ROOT_DIR / env_path
        return env_path

    active_link = ROOT_DIR / ".env.active"
    if active_link.exists():
        return active_link.resolve()

    return ROOT_DIR / _default_profile_file()


def _must_get(name: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    raise RuntimeError(f"Missing required secret: {name}")


def _get_optional(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is None:
        return default
    return value


ENV_FILE = _resolve_env_file()
if not ENV_FILE.exists():
    raise RuntimeError(
        f"Secrets file not found: {ENV_FILE}. Use ./set_env.sh <profile> or create the file."
    )

# Load selected profile.
load_dotenv(ENV_FILE, override=True)

PROJECT_ID = _must_get("PROJECT_ID")
KEY1 = _must_get("KEY1")
COMPARTMENT_ID = _must_get("COMPARTMENT_ID")
LANGFUSE_SECRET_KEY = _get_optional("LANGFUSE_SECRET_KEY", "")
LANGFUSE_PUBLIC_KEY = _get_optional("LANGFUSE_PUBLIC_KEY", "")
VECTOR_STORE_ID = _get_optional("VECTOR_STORE_ID", "")
