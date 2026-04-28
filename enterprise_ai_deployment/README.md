# OCI Enterprise AI Deployment Menu

This folder contains a first text-based utility to manage OCI Enterprise AI
resources through the OCI CLI.

Available operations:

- get hosted application details;
- get hosted deployment details;
- list hosted applications by region and compartment;
- create a hosted application;
- create a hosted deployment inside a hosted application.

This first version calls the OCI CLI directly:

- `oci generative-ai hosted-application get`
- `oci generative-ai hosted-application-collection list-hosted-applications`
- `oci generative-ai hosted-application create`
- `oci generative-ai hosted-deployment get`
- `oci generative-ai hosted-deployment create`
- `oci generative-ai hosted-deployment create-hosted-deployment-single-docker-artifact`

## Prerequisites

- active or available `agent_hub` Conda environment;
- OCI CLI installed and updated in the `agent_hub` environment;
- valid OCI config file, usually `~/.oci/config`;
- IAM policies that allow reading and creating Generative AI resources;
- target compartment OCID.

Quick check:

```bash
oci --version
oci generative-ai hosted-application --help
```

## Configuration

The menu reads a few optional environment variables:

```bash
export OCI_CLI_PROFILE=DEFAULT
export OCI_CLI_REGION=us-chicago-1
export OCI_COMPARTMENT_ID=ocid1.compartment.oc1...
```

Supported aliases:

- `OCI_PROFILE`, when `OCI_CLI_PROFILE` is not set;
- `OCI_REGION`, when `OCI_CLI_REGION` is not set;
- `COMPARTMENT_ID`, when `OCI_COMPARTMENT_ID` is not set.

If profile or region are not configured through environment variables, the OCI
CLI defaults are used.

When an operation asks for a compartment, you can enter either the compartment
OCID or its name. Names are resolved through `oci iam compartment list`; if
multiple compartments have the same name, the menu asks which one to use.

## Run

From the repository root:

```bash
python -m enterprise_ai_deployment.menu
```

The menu uses Rich for panels, tables, colors, command rendering, and JSON
output. Set `NO_COLOR=1` to disable colors, or `AGENT_HUB_MENU_COLOR=1` to
force colors in compatible terminal sessions.

The default menu/output width is 96 columns. To make OCIDs easier to copy from
the rendered output, you can increase it:

```bash
export AGENT_HUB_MENU_WIDTH=120
```

OCI commands and JSON results are printed without Rich hard-wrapping so long
OCIDs remain copy-friendly.

## Hosted Application Creation

The menu asks for:

- display name;
- compartment name or OCID;
- optional description.

It also lets you pass optional JSON files for OCI CLI complex parameters:

- scaling config;
- inbound auth config;
- networking config;
- storage configs;
- environment variables.

To generate examples for the payloads expected by the CLI:

```bash
oci generative-ai hosted-application create \
  --generate-param-json-input scaling-config

oci generative-ai hosted-application create \
  --generate-param-json-input inbound-auth-config

oci generative-ai hosted-application create \
  --generate-param-json-input networking-config

oci generative-ai hosted-application create \
  --generate-param-json-input storage-configs

oci generative-ai hosted-application create \
  --generate-param-json-input environment-variables
```

Save the JSON in a local file, edit it, then enter its path in the menu. The
program automatically converts the path to `file://...` for OCI CLI.

## Hosted Deployment Creation

The menu supports two modes:

1. full active artifact JSON, passed to `--active-artifact`;
2. guided Docker mode, with container URI and tag, using the
   `create-hosted-deployment-single-docker-artifact`.

To generate an active artifact example:

```bash
oci generative-ai hosted-deployment create \
  --generate-param-json-input active-artifact
```

## Security Notes

The menu does not store secrets and does not write OCIDs to the repository.
Create operations ask for confirmation before running the OCI CLI.

Before working on shared resources, always verify the active profile:

```bash
./show_current_env.sh
```
