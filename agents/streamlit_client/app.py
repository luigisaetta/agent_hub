"""
Author: L. Saetta
Last modified: 2026-04-14
License: MIT

Description:
    Streamlit generalized client to test OCI Enterprise AI agent endpoints,
    with optional JWT token retrieval via confidential application credentials.
"""

# pylint: disable=wrong-import-position,broad-exception-caught,import-error

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Ensure repository root is importable when Streamlit runs this file directly.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config import REGION  # noqa: E402
from agents.streamlit_client.runtime import (  # noqa: E402
    derive_agent_url,
    invoke_agent,
    parse_env_key_values,
    parse_payload_text,
    request_access_token,
    select_important_jwt_claims,
)

USE_JWT_KEY = "agent_client_use_jwt"
CLIENT_ID_KEY = "agent_client_client_id"
CLIENT_SECRET_KEY = "agent_client_client_secret"
GENAI_APP_ID_KEY = "agent_client_genai_app_id"
REGION_KEY = "agent_client_region"
AGENT_URL_KEY = "agent_client_agent_url"
ENDPOINT_PATH_KEY = "agent_client_endpoint_path"
PAYLOAD_KEY = "agent_client_payload"
OCI_DOMAIN_URL_KEY = "agent_client_oci_domain_url"
OCI_SCOPE_KEY = "agent_client_oci_scope"
OCI_TOKEN_URL_KEY = "agent_client_oci_token_url"
REQUEST_TIMEOUT_KEY = "agent_client_request_timeout"
SHOW_JWT_CLAIMS_KEY = "agent_client_show_jwt_claims"
ENV_UPLOAD_KEY = "agent_client_env_upload"

DEFAULT_PAYLOAD = '{\n  "user_request": "Hello from Streamlit"\n}'
DEFAULT_SCOPE = "urn:opc:resource:consumer::all"
DEFAULT_TIMEOUT_SECONDS = 120

ENV_TO_UI_MAPPING = {
    "AGENT_URL": AGENT_URL_KEY,
    "GENAI_APPLICATION_ID": GENAI_APP_ID_KEY,
    "REGION": REGION_KEY,
    "OCI_CLIENT_ID": CLIENT_ID_KEY,
    "OCI_CLIENT_SECRET": CLIENT_SECRET_KEY,
    "OCI_DOMAIN_URL": OCI_DOMAIN_URL_KEY,
    "OCI_SCOPE": OCI_SCOPE_KEY,
    "OCI_TOKEN_URL": OCI_TOKEN_URL_KEY,
}


def _init_session_state() -> None:
    """Initialize state keys used by this page."""
    defaults = {
        USE_JWT_KEY: False,
        CLIENT_ID_KEY: "",
        CLIENT_SECRET_KEY: "",
        GENAI_APP_ID_KEY: "",
        REGION_KEY: REGION,
        AGENT_URL_KEY: "",
        ENDPOINT_PATH_KEY: "/actions/invoke/chat",
        PAYLOAD_KEY: DEFAULT_PAYLOAD,
        OCI_DOMAIN_URL_KEY: "",
        OCI_SCOPE_KEY: DEFAULT_SCOPE,
        OCI_TOKEN_URL_KEY: "",
        REQUEST_TIMEOUT_KEY: DEFAULT_TIMEOUT_SECONDS,
        SHOW_JWT_CLAIMS_KEY: False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _refresh_derived_url() -> None:
    """Recompute URL from GenAI app id, unless the id is empty."""
    genai_app_id = str(st.session_state[GENAI_APP_ID_KEY]).strip()
    region = str(st.session_state[REGION_KEY]).strip()
    endpoint_path = str(st.session_state[ENDPOINT_PATH_KEY]).strip()
    if not genai_app_id or not region:
        return
    st.session_state[AGENT_URL_KEY] = derive_agent_url(
        region=region,
        genai_application_id=genai_app_id,
        endpoint_path=endpoint_path,
    )


def _apply_env_mapping(env_values: dict[str, str]) -> tuple[list[str], list[str]]:
    """Map .env vars to Streamlit UI state keys."""
    mapped: list[str] = []
    ignored: list[str] = []

    for env_key, state_key in ENV_TO_UI_MAPPING.items():
        if env_key in env_values:
            st.session_state[state_key] = env_values[env_key]
            mapped.append(env_key)

    timeout_value = env_values.get("REQUEST_TIMEOUT_SECONDS")
    if timeout_value is not None:
        try:
            timeout_seconds = int(timeout_value)
        except ValueError:
            ignored.append("REQUEST_TIMEOUT_SECONDS")
        else:
            st.session_state[REQUEST_TIMEOUT_KEY] = max(10, min(600, timeout_seconds))
            mapped.append("REQUEST_TIMEOUT_SECONDS")

    if any(
        env_values.get(key)
        for key in (
            "OCI_CLIENT_ID",
            "OCI_CLIENT_SECRET",
            "OCI_DOMAIN_URL",
            "OCI_SCOPE",
        )
    ):
        st.session_state[USE_JWT_KEY] = True

    for env_key in env_values:
        if env_key not in mapped and env_key not in ignored:
            ignored.append(env_key)

    return mapped, ignored


def _render_env_drag_drop() -> None:
    """Render .env drag&drop uploader and apply mapping to UI values."""
    st.caption("Drag and drop a `.env` file to automatically populate UI fields")
    uploaded = st.file_uploader(
        "File `.env` client",
        key=ENV_UPLOAD_KEY,
        type=["env", "local", "txt"],
        help=(
            "Supports for example `agents/hello_world/.env.client_jwt.local` "
            "or equivalent files."
        ),
    )
    if uploaded is None:
        return

    try:
        env_text = uploaded.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        st.error("Unable to read file: please use UTF-8 encoding.")
        return

    env_values = parse_env_key_values(env_text)
    if not env_values:
        st.warning("No valid variables found in the .env file.")
        return

    st.caption(f"Variables found: {len(env_values)}")
    if st.button("Populate UI from .env file", use_container_width=True):
        mapped, ignored = _apply_env_mapping(env_values)
        if mapped:
            st.success("Updated fields: " + ", ".join(sorted(mapped)))
        if ignored:
            st.info("Ignored variables: " + ", ".join(sorted(ignored)))


def _render_sidebar() -> dict[str, str | bool | int]:
    """Render sidebar and return normalized runtime configuration."""
    with st.sidebar:
        st.subheader("Agent Runtime Configuration")
        _render_env_drag_drop()
        st.divider()

        st.text_input(
            "GenAI application id",
            key=GENAI_APP_ID_KEY,
            placeholder="ocid1.generativeaihostedapplication...",
            on_change=_refresh_derived_url,
        )
        st.text_input(
            "region",
            key=REGION_KEY,
            on_change=_refresh_derived_url,
        )
        st.text_input(
            "Agent URL (derived, editable)",
            key=AGENT_URL_KEY,
            placeholder=(
                "https://inference.generativeai.<region>.oci.oraclecloud.com/"
                "20251112/hostedApplications/<app_id>/actions/invoke/chat"
            ),
        )
        st.text_input(
            "Agent endpoint path",
            key=ENDPOINT_PATH_KEY,
            placeholder="/actions/invoke/chat",
            on_change=_refresh_derived_url,
        )

        st.divider()
        st.subheader("JWT Configuration")
        use_jwt = st.toggle("Create JWT token", key=USE_JWT_KEY)
        st.text_input("client_id", key=CLIENT_ID_KEY, disabled=not use_jwt)
        st.text_input(
            "client_secret",
            key=CLIENT_SECRET_KEY,
            type="password",
            disabled=not use_jwt,
        )
        st.text_input(
            "OCI domain URL",
            key=OCI_DOMAIN_URL_KEY,
            placeholder="https://<identity-domain>",
            disabled=not use_jwt,
        )
        st.text_input(
            "OCI scope",
            key=OCI_SCOPE_KEY,
            disabled=not use_jwt,
        )
        st.text_input(
            "OCI token URL (optional)",
            key=OCI_TOKEN_URL_KEY,
            disabled=not use_jwt,
        )
        st.toggle(
            "Show important JWT claims",
            key=SHOW_JWT_CLAIMS_KEY,
            disabled=not use_jwt,
        )
        st.number_input(
            "Request timeout (seconds)",
            min_value=10,
            max_value=600,
            step=5,
            key=REQUEST_TIMEOUT_KEY,
        )

    return {
        "use_jwt": bool(st.session_state[USE_JWT_KEY]),
        "client_id": str(st.session_state[CLIENT_ID_KEY]).strip(),
        "client_secret": str(st.session_state[CLIENT_SECRET_KEY]).strip(),
        "genai_application_id": str(st.session_state[GENAI_APP_ID_KEY]).strip(),
        "region": str(st.session_state[REGION_KEY]).strip(),
        "agent_url": str(st.session_state[AGENT_URL_KEY]).strip(),
        "endpoint_path": str(st.session_state[ENDPOINT_PATH_KEY]).strip(),
        "oci_domain_url": str(st.session_state[OCI_DOMAIN_URL_KEY]).strip(),
        "oci_scope": str(st.session_state[OCI_SCOPE_KEY]).strip(),
        "oci_token_url": str(st.session_state[OCI_TOKEN_URL_KEY]).strip(),
        "request_timeout_seconds": int(st.session_state[REQUEST_TIMEOUT_KEY]),
        "show_jwt_claims": bool(st.session_state[SHOW_JWT_CLAIMS_KEY]),
    }


def _validate_runtime_config(runtime_config: dict[str, str | bool | int]) -> None:
    """Validate required fields and raise clear messages on missing values."""
    if not runtime_config["agent_url"]:
        raise ValueError("Agent URL is required.")

    if runtime_config["use_jwt"]:
        required_labels = {
            "client_id": "client_id",
            "client_secret": "client_secret",
            "oci_domain_url": "OCI domain URL",
            "oci_scope": "OCI scope",
        }
        missing = [
            label
            for key, label in required_labels.items()
            if not str(runtime_config[key]).strip()
        ]
        if missing:
            raise ValueError(
                "Missing required JWT fields: " + ", ".join(sorted(missing))
            )


def main() -> None:
    """Render Streamlit page and invoke the configured agent endpoint."""
    st.set_page_config(page_title="Agent Generalized Client", page_icon="Robot")
    st.title("OCI Enterprise AI Agent - Streamlit Client")
    st.write(
        "Configure endpoint/authentication in sidebar, edit payload below, and run "
        "the invocation."
    )

    _init_session_state()
    runtime_config = _render_sidebar()

    payload_text = st.text_area(
        "Payload (JSON or plain text)",
        key=PAYLOAD_KEY,
        height=220,
    )
    submit = st.button("Invoke Agent", type="primary")

    answer_placeholder = st.empty()
    metadata_placeholder = st.empty()

    if not submit:
        return

    try:

        def _on_delta(text: str) -> None:
            """Render streamed deltas while the response is in progress."""
            answer_placeholder.markdown(text)

        _validate_runtime_config(runtime_config)
        payload = parse_payload_text(payload_text)
        access_token = ""
        jwt_payload: dict[str, object] = {}

        if runtime_config["use_jwt"]:
            with st.spinner("Requesting JWT token..."):
                token_url, access_token, jwt_payload = request_access_token(
                    token_config={
                        "oci_domain_url": str(runtime_config["oci_domain_url"]),
                        "oci_client_id": str(runtime_config["client_id"]),
                        "oci_client_secret": str(runtime_config["client_secret"]),
                        "oci_scope": str(runtime_config["oci_scope"]),
                        "oci_token_url": str(runtime_config["oci_token_url"]),
                    }
                )
            st.success(f"JWT token acquired from: {token_url}")
            if bool(runtime_config["show_jwt_claims"]):
                with st.expander("Important JWT claims", expanded=False):
                    st.json(select_important_jwt_claims(jwt_payload))

        with st.spinner("Invoking agent endpoint..."):
            result = invoke_agent(
                agent_url=str(runtime_config["agent_url"]),
                payload=payload,
                request_timeout_seconds=int(runtime_config["request_timeout_seconds"]),
                access_token=access_token,
                on_delta=_on_delta,
            )

        final_text = str(result.get("final_output_text", "")).strip()
        if not final_text:
            final_text = "<empty>"
        answer_placeholder.markdown(final_text)

        metadata_placeholder.container()
        with metadata_placeholder:
            st.subheader("Invocation Result")
            st.write(f"URL: `{runtime_config['agent_url']}`")
            st.write(f"Events parsed: {len(result.get('events', []))}")
            st.code(final_text)
            with st.expander("Parsed SSE events", expanded=False):
                st.json(result.get("events", []))

    except Exception as exc:
        st.error(f"Invocation failed: {exc}")


if __name__ == "__main__":
    main()
