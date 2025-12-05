# Initial Setup Guide

This guide covers the one-time setup required to configure the infrastructure system. Once set up, deployments are handled automatically via GitHub Actions.

## Prerequisites

- [Python 3.11+](https://www.python.org/downloads/)
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- [Pulumi CLI](https://www.pulumi.com/docs/get-started/install/) (for local development only)
- Access to:
  - Cloudflare account with R2 enabled
  - Aiven account with API token
  - GCP project with Pub/Sub API enabled

## R2 Backend Setup

Pulumi state is stored in Cloudflare R2 (S3-compatible storage).

### Create R2 Bucket

1. Go to https://dash.cloudflare.com → R2 → Overview
2. Create bucket: `clustera-infrastructure-pulumi`
3. Create R2 API Token:
   - R2 → Manage R2 API Tokens → Create API Token
   - Permissions: **Object Read & Write**
   - Save the **Access Key ID** and **Secret Access Key**

### R2 Environment Variables

```bash
AWS_ACCESS_KEY_ID=<your-r2-access-key-id>
AWS_SECRET_ACCESS_KEY=<your-r2-secret-access-key>
AWS_REGION=auto
AWS_ENDPOINT_URL_S3=https://<account-id>.r2.cloudflarestorage.com
```

## Aiven Setup

Get your Aiven API token from the Aiven console and note your project/service names.

```bash
AIVEN_TOKEN=<your-aiven-token>
```

## GCP Setup

### Create Service Account

```bash
# Create service account
gcloud iam service-accounts create pulumi-infrastructure \
  --display-name="Pulumi Infrastructure"

# Grant Pub/Sub permissions
gcloud projects add-iam-policy-binding your-gcp-project-id \
  --member="serviceAccount:pulumi-infrastructure@your-project.iam.gserviceaccount.com" \
  --role="roles/pubsub.admin"

# Create and download key
gcloud iam service-accounts keys create gcp-key.json \
  --iam-account=pulumi-infrastructure@your-project.iam.gserviceaccount.com
```

## GitHub Secrets

Configure these secrets in GitHub repository settings (Settings → Secrets and variables → Actions):

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | R2 access key |
| `AWS_SECRET_ACCESS_KEY` | R2 secret key |
| `AWS_ENDPOINT_URL_S3` | R2 endpoint URL |
| `PULUMI_CONFIG_PASSPHRASE` | Passphrase for encrypting stack secrets |
| `AIVEN_TOKEN` | Aiven API token |
| `GCP_SERVICE_ACCOUNT_KEY` | GCP service account JSON key (contents, not path) |

## Stack Configuration

Each environment has a config file (`Pulumi.{stack}.yaml`):

```yaml
config:
  clustera-infrastructure:aiven_project: clustera-creators
  clustera-infrastructure:kafka_service: kafka-clustera
  clustera-infrastructure:gcp_project: clustera-data-plane
  gcp:project: clustera-data-plane
  gcp:region: us-central1
```

## Initialize New Stacks

To add a new environment stack:

```bash
source .env
pulumi login "s3://clustera-infrastructure-pulumi?endpoint=$AWS_ENDPOINT_URL_S3"
pulumi stack init <stack-name>
```

Then create `Pulumi.<stack-name>.yaml` with the appropriate configuration.
