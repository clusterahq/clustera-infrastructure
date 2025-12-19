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

### For GitHub Actions: Workload Identity Federation (Recommended)

Use the provided script to set up Workload Identity Federation:

```bash
# Run the setup script (requires GCP org admin or project owner)
./setup-gcp-workload-identity-v3.sh clustera-control-plane clusterahq clustera-infrastructure

# This will output values for:
# - GCP_WORKLOAD_IDENTITY_PROVIDER
# - GCP_SERVICE_ACCOUNT
```

**Benefits:**
- ✅ No service account keys to manage or rotate
- ✅ More secure (short-lived tokens)
- ✅ Complies with GCP security best practices

### For Local Development: Use Personal Credentials

Authenticate with your personal GCP account and use service account impersonation:

```bash
# 1. Authenticate with your personal account
gcloud auth application-default login --project=clustera-control-plane

# 2. Grant yourself permission to impersonate the service account (one-time)
gcloud iam service-accounts add-iam-policy-binding \
  pulumi-infrastructure@clustera-control-plane.iam.gserviceaccount.com \
  --member=user:YOUR_EMAIL@clustera.io \
  --role=roles/iam.serviceAccountTokenCreator

# 3. Add to your .env file:
# export GOOGLE_IMPERSONATE_SERVICE_ACCOUNT=pulumi-infrastructure@clustera-control-plane.iam.gserviceaccount.com
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
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Workload Identity Provider resource name |
| `GCP_SERVICE_ACCOUNT` | Service account email |

## Stack Configuration

Each environment has a config file (`Pulumi.{stack}.yaml`):

```yaml
config:
  clustera-infrastructure:aiven_project: clustera-creators
  clustera-infrastructure:kafka_service: kafka-clustera
  clustera-infrastructure:gcp_project: clustera-control-plane
  gcp:project: clustera-control-plane
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
