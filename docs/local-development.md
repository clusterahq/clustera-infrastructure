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

For local development, you can use your personal GCP credentials:

```bash
gcloud auth application-default login
```

Or use a service account key:
```bash
export GOOGLE_CREDENTIALS=/path/to/gcp-key.json
```

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
echo $GOOGLE_CREDENTIALS
```

### Import Existing Resources

To import a resource that exists in the cloud but not in Pulumi state:
```bash
pulumi import gcp:pubsub/topic:Topic <resource-name> projects/<project>/topics/<topic-name>
```
