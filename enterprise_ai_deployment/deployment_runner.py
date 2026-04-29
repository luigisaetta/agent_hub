"""
Author: L. Saetta
Last modified: 2026-04-29
License: MIT

Description:
    Non-interactive orchestration for the OCI Enterprise AI deployment CLI.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

from enterprise_ai_deployment.cli_commands import (
    HostedApplicationCreateRequest,
    HostedApplicationJsonOptions,
    build_create_hosted_application_command,
)
from enterprise_ai_deployment.config import OciCliConfig
from enterprise_ai_deployment.deployment_config import (
    DeploymentConfig,
    DeploymentConfigError,
    load_deployment_config,
)
from enterprise_ai_deployment.deployment_renderer import (
    RenderedArtifacts,
    render_artifacts,
)
from enterprise_ai_deployment.deployment_validation import (
    DeploymentValidationError,
    validate_deployment_config,
)
from enterprise_ai_deployment.ocir import ImageReference, build_image_reference


@dataclass(frozen=True)
class DeploymentContext:
    """Resolved deployment inputs shared by command handlers."""

    config: DeploymentConfig
    image_reference: ImageReference
    artifacts: RenderedArtifacts | None = None


def build_parser() -> argparse.ArgumentParser:
    """Build the non-interactive deployment CLI parser."""
    parser = argparse.ArgumentParser(
        description="Deploy OCI Enterprise AI Hosted Applications from YAML."
    )
    parser.add_argument("--config", required=True, help="Path to deployment YAML.")
    parser.add_argument(
        "--env-file", help="Optional local .env file with secret references."
    )
    parser.add_argument("--output-dir", default="enterprise_ai_deployment/generated")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--non-interactive", action="store_true")
    parser.add_argument("--verbose", action="store_true")

    subparsers = parser.add_subparsers(dest="command", required=True)
    for command_name in (
        "validate",
        "render",
        "build",
        "push",
        "create-application",
        "create-deployment",
        "deploy",
    ):
        subparsers.add_parser(command_name)
    rollback = subparsers.add_parser("rollback")
    rollback.add_argument("--to-tag", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the deployment CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run_command(args)
    except (DeploymentConfigError, DeploymentValidationError, RuntimeError) as exc:
        print(f"Error: {exc}")
        return 1


def run_command(args: argparse.Namespace) -> int:
    """Dispatch one parsed CLI command."""
    context = _prepare_context(
        args, render=args.command in {"render", "create-application", "deploy"}
    )

    if args.command == "validate":
        print("Configuration is valid.")
        return 0
    if args.command == "render":
        _print_rendered(context.artifacts)
        return 0
    if args.command == "create-application":
        return create_hosted_application(context, args)
    if args.command == "deploy":
        _print_plan(context)
        if args.dry_run:
            print("Dry run: Hosted Application creation command was not executed.")
            return 0
        return create_hosted_application(context, args)

    print(f"Command {args.command!r} is not implemented in this first task.")
    return 0


def create_hosted_application(
    context: DeploymentContext, args: argparse.Namespace
) -> int:
    """Create the Hosted Application through OCI CLI, or print it in dry-run mode."""
    if context.artifacts is None:
        raise RuntimeError(
            "Artifacts must be rendered before creating a Hosted Application."
        )
    config = context.config
    artifacts = context.artifacts
    command = build_create_hosted_application_command(
        OciCliConfig(region=config.application.region),
        HostedApplicationCreateRequest(
            display_name=config.hosted_application.display_name,
            compartment_id=config.application.compartment_id,
            description=config.hosted_application.description,
            json_options=HostedApplicationJsonOptions(
                scaling_config=(
                    str(artifacts.scaling_config) if artifacts.scaling_config else None
                ),
                inbound_auth_config=(
                    str(artifacts.inbound_auth_config)
                    if artifacts.inbound_auth_config
                    else None
                ),
                networking_config=(
                    str(artifacts.networking_config)
                    if artifacts.networking_config
                    else None
                ),
                environment_variables=(
                    str(artifacts.environment_variables)
                    if artifacts.environment_variables
                    else None
                ),
            ),
            wait=config.hosted_deployment.wait_for_state is not None,
        ),
    )
    print()
    print("OCI CLI command:\n")
    print(format_command(command))
    print()
    if args.dry_run:
        print("Dry run: command not executed.")
        return 0

    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.stdout:
        print(_pretty_json(result.stdout))
    if result.stderr:
        print(result.stderr.strip())
    if result.returncode != 0:
        raise RuntimeError(
            "create-application failed. Verify OCI CLI configuration, IAM policies, "
            "compartment, and Hosted Application JSON payloads."
        )
    return 0


def _prepare_context(args: argparse.Namespace, render: bool) -> DeploymentContext:
    """Load, validate, resolve image reference, and optionally render artifacts."""
    config = load_deployment_config(args.config, env_file=args.env_file)
    validate_deployment_config(config)
    image_reference = build_image_reference(config)
    artifacts = (
        render_artifacts(config, image_reference, args.output_dir) if render else None
    )
    return DeploymentContext(
        config=config, image_reference=image_reference, artifacts=artifacts
    )


def _print_rendered(artifacts: RenderedArtifacts | None) -> None:
    """Print generated artifact paths."""
    if artifacts is None:
        return
    print("Generated OCI CLI JSON artifacts:")
    for path in _artifact_paths(artifacts):
        print(f"- {path}")


def _print_plan(context: DeploymentContext) -> None:
    """Print a concise deployment plan."""
    print("Deployment plan:")
    print(f"- application: {context.config.hosted_application.display_name}")
    print(f"- compartment: {context.config.application.compartment_id}")
    print(f"- image: {context.image_reference.image_uri}")
    _print_rendered(context.artifacts)


def _artifact_paths(artifacts: RenderedArtifacts) -> list[Path]:
    """Return non-empty artifact paths in a stable order."""
    return [
        path
        for path in (
            artifacts.hosted_application_create,
            artifacts.hosted_deployment_create,
            artifacts.scaling_config,
            artifacts.inbound_auth_config,
            artifacts.networking_config,
            artifacts.environment_variables,
            artifacts.active_artifact,
        )
        if path is not None
    ]


def format_command(command: list[str]) -> str:
    """Return a shell-safe display form for a command argument list."""
    return shlex.join(command)


def _pretty_json(text: str) -> str:
    """Pretty-print JSON output when possible."""
    try:
        return json.dumps(json.loads(text), indent=2, sort_keys=True)
    except json.JSONDecodeError:
        return text.strip()
