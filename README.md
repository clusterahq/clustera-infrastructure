# Clustera Infrastructure

Pulumi-based infrastructure as code for the Clustera platform. This project manages:
- Aiven Kafka topics for event streaming
- GCP Pub/Sub topics and subscriptions for notifications

## Prerequisites

- [Python 3.11+](https://www.python.org/downloads/)
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- [Pulumi CLI](https://www.pulumi.com/docs/get-started/install/)
- [AWS CLI](https://aws.amazon.com/cli/) - For S3 state backend
- Access to:
  - Aiven account with API token
  - GCP project with Pub/Sub API enabled
  - AWS S3 bucket for Pulumi state storage

## Project Structure

```
clustera-infrastructure/
├── Pulumi.yaml                        # Project definition with S3 backend
├── Pulumi.development.yaml.example    # Example development stack config
├── Pulumi.testing.yaml.example        # Example testing stack config
├── Pulumi.staging.yaml.example        # Example staging stack config
├── Pulumi.prod.yaml.example           # Example production stack config
├── pyproject.toml                     # Python dependencies (uv)
├── Makefile                           # Helper commands for common tasks
├── __main__.py                        # Main Pulumi program entry point
├── infrastructure/                    # Infrastructure modules
│   ├── __init__.py
│   ├── kafka.py                       # Aiven Kafka topics
│   └── pubsub.py                      # GCP Pub/Sub topics
├── .env.example                       # Environment variables template
└── README.md                          # This file
```

## Setup

### 1. Install Dependencies

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python dependencies
uv sync
# OR use the Makefile
make install
```

### 2. Configure Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:
- **AWS credentials** - For S3 backend state storage
- **PULUMI_ACCESS_TOKEN** - From [Pulumi Cloud](https://app.pulumi.com/account/tokens) (optional, if using Pulumi Cloud)
- **AIVEN_TOKEN** - Your Aiven API token
- **GOOGLE_CREDENTIALS** - Path to your GCP service account key JSON

Load the environment variables:

```bash
source .env  # or use direnv for automatic loading
```

### 3. Set Up S3 Backend

Create an S3 bucket for Pulumi state storage:

```bash
# Replace with your desired bucket name
aws s3 mb s3://clustera-pulumi-state --region us-east-1

# Enable versioning (recommended)
aws s3api put-bucket-versioning \
  --bucket clustera-pulumi-state \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket clustera-pulumi-state \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

Update `Pulumi.yaml` if you used a different bucket name:

```yaml
backend:
  url: s3://your-bucket-name
```

### 4. Initialize Pulumi Stack

Create and configure a new stack. Clustera uses four environments:
- `development` - Development environment
- `testing` - Testing/QA environment
- `staging` - Pre-production staging
- `prod` - Production environment

```bash
# Login to S3 backend
pulumi login s3://clustera-pulumi-state

# Initialize a new stack (choose one: development, testing, staging, prod)
pulumi stack init development

# Copy example config and customize
cp Pulumi.development.yaml.example Pulumi.development.yaml

# Edit Pulumi.development.yaml with your actual values
# - Aiven project name and Kafka service name
# - GCP project ID and region
```

Configure the stack:

```bash
# Set Aiven configuration
pulumi config set aiven_project your-aiven-project-name
pulumi config set kafka_service your-kafka-service-name

# Set GCP configuration
pulumi config set gcp_project your-gcp-project-id
pulumi config set gcp:project your-gcp-project-id
pulumi config set gcp:region us-central1

# Set AWS region (for S3 backend)
pulumi config set aws:region us-east-1
```

### 5. Verify GCP Setup

Ensure your GCP service account has the necessary permissions:

```bash
# Authenticate with GCP
gcloud auth activate-service-account --key-file=$GOOGLE_CREDENTIALS

# Enable Pub/Sub API if not already enabled
gcloud services enable pubsub.googleapis.com --project=your-gcp-project-id

# Verify permissions
gcloud projects get-iam-policy your-gcp-project-id \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:*"
```

Required IAM roles for the service account:
- `roles/pubsub.admin` or `roles/pubsub.editor`

## Usage

> **Tip:** Use `make help` to see all available Makefile commands for common tasks.

### Preview Changes

Preview infrastructure changes before applying:

```bash
pulumi preview
# OR
make preview
```

### Deploy Infrastructure

Deploy the infrastructure:

```bash
pulumi up
# OR
make up
```

Review the changes and confirm when prompted.

### View Outputs

After deployment, view the stack outputs:

```bash
pulumi stack output

# Or get specific output
pulumi stack output kafka_topic_name
pulumi stack output pubsub_topic_name
```

### Refresh State

Sync Pulumi state with actual cloud resources:

```bash
pulumi refresh
```

### Destroy Infrastructure

Remove all resources:

```bash
pulumi destroy
```

## Multiple Environments

Clustera uses four environments: development, testing, staging, and prod.

To set up additional stacks:

```bash
# Create testing stack
pulumi stack init testing
cp Pulumi.testing.yaml.example Pulumi.testing.yaml
# Edit Pulumi.testing.yaml with testing values

# Create staging stack
pulumi stack init staging
cp Pulumi.staging.yaml.example Pulumi.staging.yaml
# Edit Pulumi.staging.yaml with staging values

# Create production stack
pulumi stack init prod
cp Pulumi.prod.yaml.example Pulumi.prod.yaml
# Edit Pulumi.prod.yaml with production values

# Switch between stacks
pulumi stack select development
pulumi stack select testing
pulumi stack select staging
pulumi stack select prod

# List all stacks
pulumi stack ls
```

## Resources Created

### Aiven Kafka

- **Topic Name**: `clustera.events.{stack}`
- **Partitions**: 3
- **Replication**: 2
- **Retention**: 7 days
- **Compression**: Snappy

### GCP Pub/Sub

- **Topic Name**: `clustera-notifications-{stack}`
- **Subscription Name**: `clustera-notifications-sub-{stack}`
- **Message Retention**: 7 days
- **Ack Deadline**: 20 seconds

## Troubleshooting

### State Lock Issues

If you encounter a state lock conflict:

```bash
pulumi cancel
```

### Authentication Errors

**Aiven**: Ensure `AIVEN_TOKEN` is set correctly:
```bash
export AIVEN_TOKEN=your_token
```

**GCP**: Verify credentials are properly set:
```bash
export GOOGLE_CREDENTIALS=/path/to/key.json
gcloud auth activate-service-account --key-file=$GOOGLE_CREDENTIALS
```

**AWS**: For S3 backend access:
```bash
aws configure
# or
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### Missing Resources

If resources aren't created, check:
1. Service quotas in GCP
2. Aiven service is running
3. Correct project IDs and service names in config

### Import Existing Resources

To import existing resources into Pulumi state:

```bash
pulumi import gcp:pubsub/topic:Topic clustera-notifications-topic projects/your-project/topics/topic-name
```

## CI/CD Integration

Example GitHub Actions workflow (`.github/workflows/pulumi.yml`):

```yaml
name: Pulumi Infrastructure
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
  AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
  AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  AIVEN_TOKEN: ${{ secrets.AIVEN_TOKEN }}
  GOOGLE_CREDENTIALS: ${{ secrets.GCP_CREDENTIALS }}

jobs:
  preview:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - uses: pulumi/actions@v5
        with:
          command: preview
          stack-name: development
          work-dir: .

  deploy-staging:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - uses: pulumi/actions@v5
        with:
          command: up
          stack-name: staging
          work-dir: .

  deploy-prod:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: production
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - uses: pulumi/actions@v5
        with:
          command: up
          stack-name: prod
          work-dir: .
```

## Development

### Add New Resources

1. Create a new module in `infrastructure/`
2. Import and use in `__main__.py`
3. Update this README

### Testing

```bash
# Install dev dependencies
uv sync --extra dev

# Run tests (when available)
pytest
```

## Support

For issues or questions:
- Pulumi: https://www.pulumi.com/docs/
- Aiven: https://docs.aiven.io/
- GCP Pub/Sub: https://cloud.google.com/pubsub/docs

## License

[Your License Here]
