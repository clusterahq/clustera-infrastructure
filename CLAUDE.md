# clustera-infrastructure

Pulumi-based Infrastructure as Code (IaC) for the Clustera platform. Manages cloud resources across Aiven (Kafka), GCP (Pub/Sub), and Cloudflare (DNS), with Cloudflare R2 for state storage.

## Quick Reference

```bash
# Setup
make install              # Install dependencies with uv
cp .env.example .env      # Create env file, fill in credentials
make init                 # Initialize Pulumi stack (interactive)

# Daily operations
make preview              # Preview changes before deploy
make up                   # Deploy infrastructure
make outputs              # View stack outputs
make refresh              # Sync state with cloud

# Stack selection
make select-dev           # Switch to development
make select-staging       # Switch to staging
make select-prod          # Switch to production
```

## Architecture Overview

```
clustera-infrastructure/
├── __main__.py                           # Pulumi entry point
├── infrastructure/
│   ├── control-plane/                    # (future) Control plane resources
│   ├── core/                             # Core shared resources
│   │   └── cloudflare.py                 # Cloudflare DNS A records
│   ├── data_plane/                       # Data plane Kafka topics
│   │   ├── kafka.py                      # Topic creation logic
│   │   └── kafka-topics.yaml             # Topic definitions
│   └── integrations/                     # Integration-specific resources
│       ├── shared/                       # Shared integration topics
│       │   ├── kafka.py                  # YAML-driven topic creation
│       │   └── kafka-topics.yaml         # Shared topic definitions
│       ├── integration-gmail/            # Gmail push notifications
│       │   ├── pubsub.py                 # GCP Pub/Sub for Gmail API
│       │   └── kafka-topics.yaml         # Gmail worker topic
│       ├── integration-slack/            # Slack integration
│       ├── integration-zoom/             # Zoom integration
│       ├── integration-google-drive/     # Google Drive integration
│       ├── integration-circle/           # Circle integration
│       └── integration-distribution/     # Distribution integration
├── Pulumi.yaml                           # Project config (R2 backend)
├── Pulumi.*.yaml.example                 # Stack config templates
├── .env.example                          # Credentials template
└── Makefile                              # Helper commands
```

## Environments (Stacks)

Deployments are **branch-based**. Each branch deploys to its corresponding stack.

| Branch | Stack | Purpose | Protection |
|--------|-------|---------|------------|
| `development` | development | Shared dev environment | None |
| `testing` | testing | Automated tests, QA | None |
| `staging` | staging | Pre-production validation | None |
| `main` | prod | Live production | **Protected** |
| `steve1` | steve1 | Personal dev (Steve) | None |

### Adding a New Personal Environment

To create a new environment (e.g., `juan1`):

1. **Add branch to workflow** (`.github/workflows/pulumi-deploy.yml`):
   ```yaml
   branches:
     - juan1  # Add to both push and pull_request sections
   ```

2. **Add stack mapping** (in both `preview` and `deploy` jobs):
   ```bash
   juan1) echo "stack=juan1" >> $GITHUB_OUTPUT ;;
   ```

3. **Create stack config** (`Pulumi.juan1.yaml`):
   ```yaml
   config:
     clustera-infrastructure:aiven_project: clustera-creators
     clustera-infrastructure:kafka_service: kafka-clustera
     clustera-infrastructure:gcp_project: clustera-control-plane
     gcp:project: clustera-control-plane
     gcp:region: us-central1
   ```

4. **Create and push the branch**:
   ```bash
   git checkout -b juan1
   git push -u origin juan1
   ```

GitHub Actions will create all topics with the `juan1-` prefix.

**GitHub Environment for Secrets**: Personal dev branches automatically use the `development` GitHub Environment for secrets (AIVEN_TOKEN, GCP_SERVICE_ACCOUNT_KEY, etc.). No additional GitHub Environment setup needed.

## Cloud Resources Managed

### Aiven Kafka Topics

Topics are defined in `kafka-topics.yaml` files and use `{stack}` substitution for environment-specific naming.

**Data Plane Topics** (`infrastructure/data_plane/kafka-topics.yaml`):
- `{stack}-runtime` - Main runtime messages (10 partitions)
- `{stack}-cerebras` - Cerebras LLM integration (10 partitions)
- `{stack}-ingestion-control` - Ingestion control plane (10 partitions)
- `{stack}-raw-records` - Raw ingested records
- `{stack}-http-requests/responses-lake` - HTTP proxy traffic
- `{stack}-websocket-requests/responses` - WebSocket proxy traffic
- `{stack}-sse-requests/responses-lake` - SSE proxy traffic
- `{stack}-nginx-*` - NGINX routing topics

**Integration Topics** (`infrastructure/integrations/*/kafka-topics.yaml`):
- `{stack}-integrations-incoming-records` - Shared incoming records
- `{stack}-integrations-errors` - Shared error handling
- `{stack}-integrations-worker-gmail` - Gmail worker queue
- `{stack}-integrations-worker-slack` - Slack worker queue
- `{stack}-integrations-worker-zoom` - Zoom worker queue
- `{stack}-integrations-worker-distribution` - Distribution worker queue
- Dead letter queues (`*-dlq`) for failed messages

**Default Topic Configuration**:
| Setting | Data Plane | Integrations |
|---------|------------|--------------|
| Partitions | 1-10 | 1 |
| Replication | 3 | 2 |
| Retention | 7 days | 3 days |
| Max Message | 25 MB | 25 MB |
| Compression | snappy | snappy |

### GCP Pub/Sub

**Gmail Integration** (`infrastructure/integrations/integration-gmail/pubsub.py`):
- Topic: `{stack}-integration-gmail-webhook`
- Subscription: `{stack}-integration-gmail-webhook-sub`
- IAM binding for `gmail-api-push@system.gserviceaccount.com`
- Push or pull subscription based on `gmail_webhook_endpoint` config

### Cloudflare DNS

**Cluster Node A Records** (`infrastructure/core/cloudflare.py`):
- Manages DNS A records for cluster nodes
- Each node can have one or more IP addresses
- Domain names configured per environment
- TTL: 300 seconds (5 minutes)
- Direct DNS (not proxied through Cloudflare)

**Configuration** (in `Pulumi.{stack}.yaml`):
```yaml
clustera-infrastructure:cloudflare_zone_id: your-zone-id
clustera-infrastructure:nodes:
  - name: "1"
    ips: ["203.0.113.1"]
    domain: "1.clustera.io"
  - name: "staging-1"
    ips: ["192.0.2.10", "192.0.2.11"]  # Multiple IPs supported
    domain: "staging-1.clustera.io"
```

**Node Configuration Fields**:
- `name`: Node identifier (e.g., "1", "staging-1", "development-2")
- `ips`: List of IP addresses (one A record created per IP)
- `domain`: Fully qualified domain name (FQDN)

## Adding New Topics

### For a New Integration

1. Create directory: `infrastructure/integrations/integration-<name>/`
2. Add `kafka-topics.yaml`:
   ```yaml
   # <Name> Integration Kafka Topics

   topics:
     - name: "{stack}-integrations-worker-<name>"
       partitions: 1
       retention_ms: "259200000"      # 3 days
       retention_bytes: "629145600"   # 600 MB
   ```
3. Topics are auto-discovered and created on next `pulumi up`

### For Data Plane

Add topic to `infrastructure/data_plane/kafka-topics.yaml`:
```yaml
  - name: "{stack}-my-new-topic"
    partitions: 1
    replication: 3
    retention_ms: "604800000"      # 7 days
    retention_bytes: "-1"          # unlimited
```

## Configuration

### Required Pulumi Config

```bash
pulumi config set aiven_project <project-name>
pulumi config set kafka_service <kafka-service-name>
pulumi config set gcp_project <gcp-project-id>
pulumi config set gcp:project <gcp-project-id>
pulumi config set gcp:region us-central1
```

### Optional Config

```bash
pulumi config set gmail_webhook_endpoint https://your-endpoint.com/webhook
pulumi config set cloudflare_zone_id <your-zone-id>
pulumi config set-all --path nodes[0].name=1 \
                       --path nodes[0].domain=1.clustera.io \
                       --path nodes[0].ips[0]=203.0.113.1
```

### Environment Variables (.env)

```bash
# R2 Backend (required)
AWS_ACCESS_KEY_ID=<r2-access-key>
AWS_SECRET_ACCESS_KEY=<r2-secret-key>
AWS_REGION=auto
AWS_ENDPOINT_URL_S3=https://<account-id>.r2.cloudflarestorage.com

# Secrets encryption
PULUMI_CONFIG_PASSPHRASE=<passphrase>

# Providers
AIVEN_TOKEN=<aiven-api-token>
GOOGLE_CREDENTIALS=keys/gcp/service-account.json
CLOUDFLARE_API_TOKEN=<cloudflare-api-token>  # Optional, for DNS management
```

## State Backend

Uses Cloudflare R2 (S3-compatible) instead of Pulumi Cloud:
- Bucket: `clustera-infrastructure-pulumi`
- Endpoint: `2d45fcd3b3e68735a6ab3542fb494c19.r2.cloudflarestorage.com`
- Zero egress fees, full control over state

## Connecting to Kafka (Topic Audit)

To list existing Kafka topics and verify management:

```bash
# Install Aiven CLI
pip install aiven-client

# Login and list topics
avn user login
avn service topic-list <kafka-service-name> --project <project-name>
```

Or use the Aiven Console: https://console.aiven.io

## CI/CD Integration

See README.md for GitHub Actions workflow examples. Key secrets needed:
- `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ENDPOINT_URL`
- `PULUMI_CONFIG_PASSPHRASE`
- `AIVEN_TOKEN`
- `GCP_CREDENTIALS` (service account JSON as string)

## Troubleshooting

### State Lock Issues
```bash
pulumi cancel
```

### Authentication Errors
```bash
# Aiven
export AIVEN_TOKEN=your_token

# GCP
export GOOGLE_CREDENTIALS=/path/to/key.json
gcloud auth activate-service-account --key-file=$GOOGLE_CREDENTIALS

# R2
pulumi login s3://clustera-infrastructure-pulumi
```

### Gmail Pub/Sub IAM Error

If you get "One or more users named in the policy do not belong to a permitted customer":

```bash
# Override org policy for the GCP project (one-time)
gcloud org-policies reset iam.allowedPolicyMemberDomains --project=<project-id>
```

## Related Documentation

- [Pulumi Python SDK](https://www.pulumi.com/docs/reference/pkg/python/pulumi/)
- [Pulumi Aiven Provider](https://www.pulumi.com/registry/packages/aiven/)
- [Pulumi GCP Provider](https://www.pulumi.com/registry/packages/gcp/)
- [Gmail API Push Notifications](https://developers.google.com/workspace/gmail/api/guides/push)
