# Design for Automated Deployment of AI Components on OCI Enterprise AI

Author: L. Saetta
Version: 1.1
Last modified: 2026-04-29

Note: in this specification, points that still need to be defined are marked as: `TBD`.

## 1. Goal

The goal is to build an automated mechanism for deploying containerized AI components on OCI Enterprise AI, for example:

- agents
- MCP servers
- API services

The deployment must be scriptable, starting from a local Docker image of the component to be distributed and ending with the creation of the required OCI resources.

The complete path includes:

- publishing the Docker image to OCIR
- creating or updating the Hosted Application
- creating the Hosted Deployment
- configuring security, environment variables, runtime parameters, and references to the container image

## 2. Core Concept

The OCI CLI can interact with Generative AI resources, including Hosted Applications and Hosted Deployments, when the CLI version is recent enough.

Deploying a component requires two main steps:

- creating and configuring the Hosted Application
- creating and configuring the Hosted Deployment

Because these steps require many parameters, passing everything manually from the command line is not convenient. The cleanest solution is to introduce a declarative configuration file read by a script.

The file describes what to deploy and how to configure it. The script translates this configuration into the correct OCI CLI commands.

The recommended pattern is:

```text
YAML -> Python -> generated JSON -> OCI CLI -> OCI Enterprise AI
```

In short:

- YAML as the human-readable source
- JSON as the generated technical format
- OCI CLI as the operational engine
- Python as the process orchestrator

## 3. OCI Resources Involved

The design mainly revolves around two OCI Enterprise AI resources:

- Hosted Application
- Hosted Deployment

The distinction between the two resources is important because some configuration belongs logically to the application, while other configuration belongs to the individual deployment.

The following table clarifies the expected mapping. Items marked as `TBD` must be checked against the actual model required by the OCI CLI and the available APIs.

| Configuration | Hosted Application | Hosted Deployment | Notes |
|---|---:|---:|---|
| Logical application name | Yes | No | Identifies the managed AI application |
| Application display name | Yes | No | Human-readable Hosted Application name |
| Compartment | Yes | Yes | Check whether both commands explicitly require the compartment |
| Container image URI | No | Yes | The deployment must point to the Docker image published to OCIR |
| Container tag | No | Yes | Must be immutable, for example git SHA, timestamp, or build id |
| Docker artifact | No | Yes | Especially for single Docker artifact mode |
| IDCS auth | Yes | No | Rendered as `inbound-auth-config` for Hosted Application |
| Environment variables | TBD | TBD | Check where OCI requires them to be configured |
| Secrets | TBD | TBD | Check whether they are supported directly or referenced through environment and Vault |
| Scaling | TBD | TBD | Check whether it belongs to the application or the deployment |
| Networking | Probably yes | TBD | Check against the service exposure model |
| Endpoint | TBD | TBD | It may be produced by the Hosted Application, the Deployment, or both, depending on the OCI model |
| Activation state | No | Yes | The deployment can be created and then activated |
| Work request and diagnostics | Yes | Yes | Both operations can generate diagnostic information |

This table does not replace the OCI CLI documentation. It is a design guide for deciding where fields should live in the YAML file and which parts the script should validate.

## 4. Proposed Architecture

The proposed design separates three layers.

### 4.1 Configuration File

A YAML file contains all inputs required for deployment.

Example:

```text
oci_ai_deploy.yaml
```

The file is readable, versionable, and usable both locally and in CI/CD.

### 4.2 Orchestration Script

A Python script reads the YAML file, validates fields, generates any intermediate JSON files, and calls the OCI CLI.

Example:

```text
oci_ai_deploy.py
```

Python can call the OCI CLI through `subprocess`, keeping behavior very close to the manual commands that have already been validated.

### 4.3 OCI CLI and Docker

The OCI CLI performs all OCI operations:

- Hosted Application creation
- Hosted Deployment creation
- final-state waiting
- retrieval of OCIDs, endpoints, work requests, and diagnostics

Docker is used for:

- building the local image
- tagging the image for OCIR
- pushing the image to OCIR

## 5. End-to-End Flow

The complete flow should be ordered as follows.

### 5.1 Initial Validation

The script checks that the following are available:

- Docker
- OCI CLI
- compatible OCI CLI version
- working OCI configuration
- valid or possible OCIR login
- valid YAML file
- compartment id
- consistent region and region key
- application name
- security parameters, when required
- IAM prerequisites satisfied by OCI admins

### 5.2 Dry Run

Before running operations that modify resources or publish images, the tool must support a `dry-run` mode.

The `dry-run` mode must be enabled through a dedicated command-line parameter:

```bash
python oci_ai_deploy.py --config oci_ai_deploy.yaml deploy --dry-run
```

In `dry-run` mode, the script must not create, update, or delete OCI resources and must not push to OCIR.

The `dry-run` mode should show:

- resolved YAML configuration
- calculated image URI
- calculated image tag
- planned Hosted Application
- planned Hosted Deployment
- JSON payloads that would be passed to the OCI CLI
- equivalent OCI CLI commands that would be executed
- existing resources, if the check is safe and read-only
- validation errors

The `dry-run` mode is especially important for CI/CD, code review, and troubleshooting because it makes it possible to validate the deployment before modifying OCI resources.

### 5.3 Docker Image Build

The script builds the Docker image using information from the YAML file.

Logical example:

```bash
docker build -f Dockerfile -t my-agent:abc1234 .
```

### 5.4 Tagging the Image for OCIR

The script builds the full OCIR image name.

Example:

```text
fra.ocir.io/<namespace>/<repository>/<image-name>:<tag>
```

The tag should be unique, for example:

- git SHA
- timestamp
- application version number
- CI/CD build id

Using `latest` for real deployments should be avoided.

### 5.5 Push to OCIR

The script pushes the image.

Example:

```bash
docker push fra.ocir.io/<namespace>/<repository>/<image-name>:<tag>
```

### 5.6 Hosted Application Creation or Reuse

The script checks whether a Hosted Application with that name already exists.

If it exists:

- retrieve the OCID
- optionally update the configuration, if the design allows it

If it does not exist:

- create a new Hosted Application
- apply runtime, security, networking, and environment-variable configuration according to the actual OCI CLI model

### 5.7 Hosted Deployment Creation

The script creates a new Hosted Deployment associated with the Hosted Application.

The Hosted Deployment points to the Docker image published to OCIR.

Main data:

- hosted application id
- compartment id
- deployment display name
- container URI
- container tag
- artifact configuration
- optional activation flag
- optional scaling configuration, if expected at this level

### 5.8 Waiting and Diagnostics

The script waits for the final state.

If deployment succeeds:

- print the Hosted Application OCID
- print the Hosted Deployment OCID
- print the image URI
- print the endpoint, if available

If deployment fails:

- print the OCI CLI error
- print the work request, if available
- print diagnostic suggestions

## 6. YAML Configuration File

The recommended format for the main file is YAML.

Reasons:

- it is more readable than JSON
- it supports nested configuration well
- it allows comments
- it is convenient for many environment variables
- it is convenient for managing multiple environments, for example dev, test, and prod
- it can be converted easily to JSON by the script

Example `oci_ai_deploy.yaml` file:

```yaml
application:
  name: my-agent-app
  compartment_id: ocid1.compartment.oc1..example
  region: eu-frankfurt-1
  region_key: fra

container:
  context: .
  dockerfile: Dockerfile
  image_name: my-agent
  repository: ai-agents
  tag_strategy: git_sha
  ocir_namespace: auto

hosted_application:
  display_name: my-agent-app
  description: Agent application deployed through OCI Enterprise AI
  create_if_missing: true
  update_if_exists: false

  scaling:
    min_instances: 1
    max_instances: 2
    metric: cpu

  networking:
    mode: public

  security:
    auth_type: IDCS_AUTH_CONFIG
    issuer_url: https://issuer.example.com
    audience: my-agent-api
    scopes:
      - my-agent-api/.default

  environment:
    variables:
      LOG_LEVEL: INFO
      OCI_REGION: eu-frankfurt-1
      AGENT_MODE: production
      MCP_SERVER_PORT: "8080"

    secrets:
      API_KEY:
        source: vault
        secret_ocid: ocid1.vaultsecret.oc1..example

hosted_deployment:
  display_name: my-agent-deployment
  create_new_version: true
  activate: true
  wait_for_state: SUCCEEDED
```

## 7. Mapping YAML to OCI CLI JSON

The OCI CLI works well with JSON, so the YAML file should not be passed directly to OCI commands.

The recommended pattern is:

```text
deploy.yaml
  -> Python script
  -> generated JSON for OCI CLI
  -> oci generative-ai hosted-application create/update
  -> oci generative-ai hosted-deployment create/update
```

For complex configuration, generated JSON files and `--from-json` are preferred.

Example:

```bash
oci generative-ai hosted-application create \
  --from-json file://generated/create-hosted-application.json
```

The exact mapping between YAML and JSON must be implemented in the Python script and validated against the real OCI CLI commands.

Typical generated files:

```text
generated/create-hosted-application.json
generated/create-hosted-deployment.json
```

The contents of the `generated` directory should not be edited manually. They can be regenerated by the script from the YAML.

## 8. Tool Commands

For local use:

```bash
python oci_ai_deploy.py --config oci_ai_deploy.yaml validate
python oci_ai_deploy.py --config oci_ai_deploy.yaml build
python oci_ai_deploy.py --config oci_ai_deploy.yaml push
python oci_ai_deploy.py --config oci_ai_deploy.yaml create-application
python oci_ai_deploy.py --config oci_ai_deploy.yaml create-deployment
python oci_ai_deploy.py --config oci_ai_deploy.yaml deploy
python oci_ai_deploy.py --config oci_ai_deploy.yaml deploy --dry-run
```

For CI/CD:

```bash
python oci_ai_deploy.py --config oci_ai_deploy.yaml deploy --non-interactive
python oci_ai_deploy.py --config oci_ai_deploy.yaml deploy --non-interactive --dry-run
```

Possible menu mode for manual use:

```text
1. Validate configuration
2. Dry run
3. Build Docker image
4. Push image to OCIR
5. Create or update Hosted Application
6. Create Hosted Deployment
7. Full deploy
8. Show current deployments
9. Rollback
```

For automation and pipelines, non-interactive commands are preferable.

## 9. Idempotency and Update Policy

The tool should be runnable again without creating unnecessary duplicate resources.

Recommended behavior:

- if the Hosted Application exists, reuse it
- if it does not exist and `create_if_missing` is true, create it
- every deployment creates a new Hosted Deployment with a unique image tag
- do not use `latest` as the main tag
- always save and print image URI, application id, and deployment id

Naming example:

```text
my-agent-app
my-agent-app-abc1234
my-agent-app-20260428153000
```

The update strategy must be explicit because some changes are safe while others can have significant impact.

Examples of behavior to define:

- if only the image changes, create a new Hosted Deployment
- if environment variables change, check whether to update the Hosted Application or create a new Hosted Deployment, `TBD`
- if IDCS auth changes, require an explicit choice or a force mode
- if networking changes, require an explicit choice or a force mode
- if the compartment changes, do not update automatically

Possible future configuration example:

```yaml
update_policy:
  application:
    allow_update: true
    require_confirmation_for_security_changes: true
  deployment:
    always_create_new: true
    activate_new_deployment: true
```

## 10. Secrets and IDCS Auth

### 10.1 Environment Variables

Environment variables must not be passed one by one from the command line.

They must live in the YAML file in declarative form.

Example:

```yaml
environment:
  variables:
    LOG_LEVEL: INFO
    MCP_SERVER_PORT: "8080"
    AGENT_MODE: production
```

The script transforms this section into the format required by the OCI CLI for the Hosted Application or the deployment, according to the exact model expected by the command.

### 10.2 Secrets

Secrets should not be written in clear text in the YAML file.

Avoid:

```yaml
API_KEY: my-secret-value
```

External references are better.

Example with OCI Vault:

```yaml
secrets:
  API_KEY:
    source: vault
    secret_ocid: ocid1.vaultsecret.oc1..example
```

Or, for local development:

```yaml
secrets:
  API_KEY:
    source: local_env
    env_name: MY_API_KEY
```

For local development, reading secrets from environment variables or from a `.env` file excluded from version control is acceptable. For shared environments or CI/CD, OCI Vault or the pipeline secret manager is preferable.

This allows the file to be versioned without exposing credentials.

Recommended checks:

- verify that `.env` is excluded from version control
- never print secrets in logs
- mask sensitive values in output
- fail if hardcoded secrets are detected in the YAML

### 10.3 IDCS Auth

IDCS auth configuration is one of the most sensitive parts of the deployment.

In the YAML file, it should be declared in a dedicated section.

Example:

```yaml
security:
  auth_type: IDCS_AUTH_CONFIG
  issuer_url: https://issuer.example.com
  audience: my-agent-api
  scopes:
    - my-agent-api/.default
```

The script must validate that `auth_type` is either `IDCS_AUTH_CONFIG` or
`NO_AUTH`, and that required fields are present when `auth_type` is
`IDCS_AUTH_CONFIG`.

Typical fields to validate:

- issuer URL
- audience
- optional client id
- optional scopes
- related OCI policies

## 11. IAM and OCIR Access

Working IAM policies are a deployment prerequisite.

This prerequisite must be satisfied by OCI admins before the tool is used in real environments.

The tool can detect some symptoms, for example authorization errors or inability to access OCIR, but it should not take responsibility for creating or modifying IAM policies.

Adequate policies are needed for:

- pushing to OCIR
- allowing the service running the deployment to read the image
- managing Hosted Applications
- managing Hosted Deployments
- optional access to Vault
- optional access to Logging
- optional access to Networking
- optional access to Object Storage, if required by the component

It is important to distinguish between:

- permissions of the identity running the deployment
- permissions of the service or runtime that must read the image and execute the component

One possible scenario is that the Docker push succeeds, but deployment fails because the service cannot read the image from OCIR. This part must be checked carefully by OCI admins.

## 12. Rollback

Rollback should be based on immutable Docker image versions.

Recommended approach:

- every build produces a unique tag
- every Hosted Deployment points to a precise tag
- the tool can list previous deployments
- rollback selects a previous deployment or creates a new deployment that points to a previous image

Example:

```bash
python oci_ai_deploy.py --config oci_ai_deploy.yaml rollback --to-tag abc1234
```

Rollback should not depend on `latest`.

## 13. Validation, Render, and Dry Run

The `validate` phase should check at least:

- `oci` available in `PATH`
- adequate OCI CLI version
- `docker` available in `PATH`
- working OCI authentication
- retrievable OCIR namespace
- syntactically valid compartment id
- region set
- region key set
- Dockerfile present
- valid YAML file
- coherent security configuration
- no hardcoded secrets
- calculable image tag
- IAM prerequisites declared as satisfied for the target environment

In addition to `validate`, adding a `render` command can be useful:

```bash
python oci_ai_deploy.py --config oci_ai_deploy.yaml render
```

The `render` command generates the intermediate JSON files without calling OCI and without building or pushing.

The `dry-run` mode instead simulates the full deployment without modifying resources:

```bash
python oci_ai_deploy.py --config oci_ai_deploy.yaml deploy --dry-run
```

Difference between commands:

| Command | Purpose | Modifies resources? |
|---|---|---:|
| `validate` | Checks configuration and prerequisites | No |
| `render` | Generates intermediate JSON | No |
| `deploy --dry-run` | Simulates the full deployment and shows what would be done | No |
| `deploy` | Runs the real deployment | Yes |

## 14. Diagnostics and Final Report

The script should produce readable output for both human use and CI/CD.

On success, it should print:

- Hosted Application OCID
- Hosted Deployment OCID
- image URI
- endpoint, if available
- work request id, if available
- final state

On error, it should print:

- failed command
- OCI CLI error
- optional work request id
- diagnostic suggestions

Producing a final report file is also useful, for example:

```text
generated/deploy-report.json
```

Suggested content:

```json
{
  "timestamp": "2026-04-29T00:00:00Z",
  "config_file": "oci_ai_deploy.yaml",
  "git_sha": "abc1234",
  "image_uri": "fra.ocir.io/example/ai-agents/my-agent:abc1234",
  "hosted_application_id": "ocid1.example...",
  "hosted_deployment_id": "ocid1.example...",
  "endpoint": "https://example.endpoint",
  "oci_cli_version": "TBD",
  "work_request_id": "TBD",
  "final_state": "SUCCEEDED"
}
```

This report is useful for audit, rollback, and troubleshooting.

## 15. Main Expected Challenges

### 15.1 OCI CLI Version

If the following command fails:

```bash
oci generative-ai hosted-application --help
```

then the CLI does not yet include the required subcommands, or the `PATH` points to an old installation.

### 15.2 IAM Permissions

IAM policies are a prerequisite that must be satisfied by OCI admins.

The tool must fail readably if permissions are insufficient, but it must not hide the problem or attempt uncontrolled workarounds.

### 15.3 OCIR Image Access

The Docker push can succeed, but deployment can fail if the service cannot read the image.

This part must be checked carefully in OCI policies.

### 15.4 IDCS Auth Configuration

IDCS auth requires consistency across domain URL, audience, scope, and access
policies.

This configuration must be validated before deployment.

### 15.5 Container Readiness

The container must be ready for a managed runtime.

Checklist:

- listens on the correct port
- does not depend on local files
- reads configuration from environment variables
- writes logs to stdout and stderr
- handles clean shutdown
- has reasonable startup time
- exposes a health endpoint, if required

### 15.6 Specific OCI CLI Command for Deployment

The main assumed commands are:

```bash
oci generative-ai hosted-application list
oci generative-ai hosted-application create
oci generative-ai hosted-application get
oci generative-ai hosted-application update

oci generative-ai hosted-deployment list
oci generative-ai hosted-deployment create
oci generative-ai hosted-deployment create-hosted-deployment-single-docker-artifact
oci generative-ai hosted-deployment get
oci generative-ai hosted-deployment update
```

`TBD`: verify which command is correct for single Docker artifact mode in the target OCI CLI version.

This is one of the most important points to validate during the first implementation because the exact command name and JSON required by the CLI can be specific to the installed version.

## 16. Project Structure

Recommended structure:

```text
oci-ai-deployer/
  oci_ai_deploy.py
  oci_ai_deploy.yaml
  schemas/
    oci_ai_deploy.schema.json
  generated/
    create-hosted-application.json
    create-hosted-deployment.json
    deploy-report.json
  examples/
    agent-dev.yaml
    agent-prod.yaml
    mcp-server-dev.yaml
  README.md
```

Meaning:

- `oci_ai_deploy.py` contains the operational logic
- `oci_ai_deploy.yaml` contains the deployment configuration
- `schemas` contains the validation schema
- `generated` contains temporary files generated by the script
- `examples` contains reusable examples for different components
- `README.md` documents installation, prerequisites, and tool usage

## 17. Role of the Python Script

The Python script is responsible for orchestrating the deployment.

Main responsibilities:

- read YAML
- validate configuration
- calculate image tag
- retrieve OCIR namespace
- build image URI
- call Docker for build, tag, and push
- generate intermediate JSON files for OCI CLI
- support `dry-run` mode
- call OCI CLI
- handle errors
- print readable final output
- produce final report

In the first version, Python can call the OCI CLI.

Conceptual example:

```python
import subprocess

subprocess.run([
    "oci",
    "generative-ai",
    "hosted-application",
    "create",
    "--from-json",
    "file://generated/create-hosted-application.json",
    "--wait-for-state",
    "SUCCEEDED"
], check=True)
```

This approach is practical because it allows reusing the same commands already tested manually.

## 18. Roadmap

### Version 1

Python plus YAML plus OCI CLI.

Goal:

- automate the end-to-end flow
- keep the logic simple
- use CLI commands that can already be tested manually
- support validation
- support intermediate JSON generation
- support `dry-run` mode
- support non-interactive mode for CI/CD

### Version 2

Add:

- complete JSON validation schema
- more advanced multi-environment management
- rollback
- structured logs
- advanced work-request diagnostics
- complete final report
- optional tighter integration with Vault or pipeline secret managers

## 19. Recommended Design Decision

The recommended solution is:

- YAML as the main declarative format
- Python as the orchestrator
- OCI CLI as the operational engine in the first version
- generated JSON as technical input for OCI CLI
- immutable image tags
- referenced secrets, not hardcoded secrets
- mandatory validation before deployment
- `dry-run` mode through a dedicated command-line parameter
- support for non-interactive mode for CI/CD
- working IAM policies as a prerequisite managed by OCI admins

## 20. Implementation

The practical implementation of the tool is guided by the separate document:

`./implementation_spec_codex.md`

That document contains incremental tasks, acceptance criteria, non-goals, repository structure, and test commands for Codex-assisted development.

## 21. Conclusion

Automating Hosted Application and Hosted Deployment through a configuration file is the most orderly way to manage deployment of AI components such as agents and MCP servers.

The main advantage is that deployment becomes:

- repeatable
- versionable
- controllable
- suitable for CI/CD
- less prone to manual errors

The `dry-run` mode makes the process safer because it shows in advance what would be executed before creating resources, updating configuration, or publishing images.
