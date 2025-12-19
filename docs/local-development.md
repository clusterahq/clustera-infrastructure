# Local Development

For most changes, you don't need to run Pulumi locally—just commit and push, and GitHub Actions handles deployment. However, if you need to run Pulumi commands directly, follow this guide.

## Setup

1. Install dependencies:
   ```bash
   make install
   # or: uv sync
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   source .env
   ```

3. Login to R2 backend:
   ```bash
   pulumi login "s3://clustera-infrastructure-pulumi?endpoint=$AWS_ENDPOINT_URL_S3"
   ```

4. Select a stack:
   ```bash
   pulumi stack select development
   ```

## Common Commands

```bash
# Preview changes (dry run)
pulumi preview
# or: make preview

# Apply changes
pulumi up
# or: make up

# View current outputs
pulumi stack output

# Refresh state from cloud
pulumi refresh

# List all stacks
pulumi stack ls

# Switch stacks
pulumi stack select staging
```

## GCP Authentication (Local)

**Recommended:** Use your personal GCP credentials with service account impersonation:

```bash
# 1. Authenticate with your personal account
gcloud auth application-default login --project=clustera-control-plane

# 2. Grant yourself permission to impersonate the service account (one-time)
gcloud iam service-accounts add-iam-policy-binding \
  pulumi-infrastructure@clustera-control-plane.iam.gserviceaccount.com \
  --member=user:YOUR_EMAIL@clustera.io \
  --role=roles/iam.serviceAccountTokenCreator

# 3. Enable impersonation in your .env
export GOOGLE_IMPERSONATE_SERVICE_ACCOUNT=pulumi-infrastructure@clustera-control-plane.iam.gserviceaccount.com
```

**Benefits:**
- ✅ No service account keys to manage
- ✅ Better audit trail (changes show your email, not a generic service account)
- ✅ Credentials automatically refresh

**Alternative:** Use your personal credentials directly (without impersonation):
```bash
gcloud auth application-default login --project=clustera-control-plane
# Don't set GOOGLE_IMPERSONATE_SERVICE_ACCOUNT
```

**Note:** Service account keys are no longer recommended due to org policy restrictions and security best practices.

## Troubleshooting

### State Lock Issues

If a deployment is stuck or failed mid-way:
```bash
pulumi cancel
```

### Authentication Errors

Verify credentials are set:
```bash
echo $AIVEN_TOKEN
echo $AWS_ACCESS_KEY_ID
echo $GOOGLE_IMPERSONATE_SERVICE_ACCOUNT

# Test GCP authentication
gcloud auth application-default print-access-token
```

If GCP auth fails, re-authenticate:
```bash
gcloud auth application-default login --project=clustera-control-plane
```

### Import Existing Resources

To import a resource that exists in the cloud but not in Pulumi state:
```bash
pulumi import gcp:pubsub/topic:Topic <resource-name> projects/<project>/topics/<topic-name>
```
