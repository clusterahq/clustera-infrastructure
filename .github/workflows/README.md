# GitHub Actions CI/CD for Pulumi

This directory contains the GitHub Actions workflow for automated Pulumi deployments.

## Branch → Stack Mapping

The workflow automatically deploys to different Pulumi stacks based on the branch:

| Branch        | Pulumi Stack  | Auto-Deploy | Approval Required |
|---------------|---------------|-------------|-------------------|
| `main`        | `production`  | Yes         | **Yes** (manual)  |
| `development` | `development` | Yes         | No                |
| `staging`     | `staging`     | Yes         | No                |
| `testing`     | `testing`     | Yes         | No                |

## Workflow Triggers

### Pull Requests
- Runs `pulumi preview` on PRs targeting deployment branches
- Posts preview results as PR comments
- No actual deployment occurs

### Push to Branch
- Runs `pulumi up` to deploy infrastructure
- Uses GitHub Environments for approval gates (production only)
- Uploads stack outputs as artifacts

## Setup Instructions

### 1. Create GitHub Environments

Go to **Settings → Environments** and create:

#### Production Environment
- Name: `production`
- **Enable "Required reviewers"**
- Add team members who can approve production deployments
- Recommended: Enable "Wait timer" (e.g., 5 minutes) for additional safety

#### Other Environments
- Name: `development`, `staging`, `testing`
- No approval required
- Auto-deploy on push

### 2. Configure Repository Secrets

Go to **Settings → Secrets and variables → Actions**

Add these **Repository secrets**:

| Secret Name                  | Description                                    | Example/Notes                                      |
|------------------------------|------------------------------------------------|----------------------------------------------------|
| `AIVEN_TOKEN`                | Aiven API token                                | Get from Aiven Console → Profile → Tokens        |
| `PULUMI_CONFIG_PASSPHRASE`   | Passphrase for encrypting stack secrets        | Use a strong random password (store in 1Password) |
| `AWS_ACCESS_KEY_ID`          | Cloudflare R2 Access Key ID                    | From R2 → Manage R2 API Tokens                    |
| `AWS_SECRET_ACCESS_KEY`      | Cloudflare R2 Secret Access Key                | From R2 → Manage R2 API Tokens                    |
| `AWS_ENDPOINT_URL_S3`        | Cloudflare R2 endpoint URL                     | `https://<account-id>.r2.cloudflarestorage.com`   |
| `GCP_SERVICE_ACCOUNT_KEY`    | GCP service account JSON key (entire file)     | Download from GCP Console → IAM → Service Accounts|

### 3. GCP Service Account Setup

The GCP service account needs these permissions:
- `roles/pubsub.admin` - Create/manage Pub/Sub topics and subscriptions

To create the service account:

```bash
# Set your GCP project
PROJECT_ID="clustera-control-plane"

# Create service account
gcloud iam service-accounts create pulumi-deploy \
    --display-name="Pulumi Deployment" \
    --project=$PROJECT_ID

# Grant Pub/Sub admin role
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:pulumi-deploy@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/pubsub.admin"

# Create and download key
gcloud iam service-accounts keys create gcp-key.json \
    --iam-account=pulumi-deploy@${PROJECT_ID}.iam.gserviceaccount.com

# Copy the entire contents of gcp-key.json to GCP_SERVICE_ACCOUNT_KEY secret
cat gcp-key.json
```

### 4. R2 Bucket Setup

Ensure the R2 bucket exists:

```bash
npx wrangler r2 bucket create clustera-infrastructure-pulumi
```

Create R2 API token with:
- Permissions: **Object Read & Write**
- Bucket: `clustera-infrastructure-pulumi`

### 5. Initialize Pulumi Stacks

Each stack must be initialized once locally before CI/CD can use it:

```bash
# Login to R2 backend
source .env
pulumi login "s3://clustera-infrastructure-pulumi?endpoint=$AWS_ENDPOINT_URL_S3"

# Initialize each stack
pulumi stack init production
pulumi stack init staging
pulumi stack init testing
pulumi stack init development

# Configure each stack (copy from examples)
cp Pulumi.prod.yaml.example Pulumi.prod.yaml
cp Pulumi.staging.yaml.example Pulumi.staging.yaml
cp Pulumi.testing.yaml.example Pulumi.testing.yaml
# Note: Pulumi.development.yaml already exists

# Edit each file with actual values
# Then run initial deployment
pulumi stack select production
pulumi up
```

## Workflow Features

### Preview on Pull Requests
- Automatic infrastructure preview when PR is opened
- Shows what will change before merging
- Posted as PR comment for easy review
- No actual changes made

### Automatic Deployment
- Push to `development`/`staging`/`testing` → Auto-deploy
- Push to `main` → Deploy to production with approval

### Production Safety
- **Manual approval required** before production deployment
- Protected Kafka topics (cannot be deleted without explicit unprotect)
- Reviewers receive notification and must approve

### Stack Outputs
- After successful deployment, stack outputs saved as artifacts
- Available for 30 days
- Contains: topic names, subscription names, etc.

## Deployment Workflow

### Non-Production (development/staging/testing)
1. Create feature branch from `development`/`staging`/`testing`
2. Make changes and push
3. Open PR → automatic preview runs
4. Review preview, get approvals
5. Merge PR → automatic deployment

### Production
1. Create PR from `staging` → `main` (or direct to `main`)
2. Automatic preview runs on PR
3. Review preview carefully
4. Merge PR → deployment job starts
5. **Designated approver must manually approve**
6. After approval, deployment proceeds
7. Protected topics prevent accidental deletion

## Monitoring Deployments

### GitHub Actions UI
- Go to **Actions** tab in repository
- Click on workflow run to see details
- Each step shows logs and timing

### Stack Outputs
- Download artifacts from completed workflow runs
- JSON file contains all Pulumi outputs
- Useful for integration with other systems

### Pulumi State
- All state stored in R2 (S3-compatible)
- Same backend used by local development and CI/CD
- Consistent state across all environments

## Troubleshooting

### "Stack not found" Error
- Stack needs to be initialized first (see step 5 above)
- Or stack config file is missing (Pulumi.{stack}.yaml)

### Authentication Failures
- Check that all secrets are configured correctly
- Verify GCP service account has correct permissions
- Test R2 access with `aws s3 ls --endpoint-url=$AWS_ENDPOINT_URL_S3`

### Preview Not Posting to PR
- Workflow needs `pull-requests: write` permission (already configured)
- Check Actions logs for errors

### Production Deployment Stuck
- Check if waiting for approval (expected behavior)
- Verify approvers are configured in production environment settings

## Security Best Practices

✅ **Secrets Management**
- All credentials stored as GitHub encrypted secrets
- Secrets never logged or exposed in workflow output
- GCP service account key written to temp file, deleted after use

✅ **Least Privilege**
- GCP service account has minimal required permissions
- R2 token scoped to specific bucket
- Aiven token should be project-scoped if possible

✅ **Production Protection**
- Manual approval gate for production
- Protected Kafka topics in production stack
- Preview before deploy workflow

✅ **Audit Trail**
- All deployments logged in GitHub Actions
- Approvals tracked with timestamp and approver
- Pulumi state includes full resource history

## Branch Protection Recommendations

Configure branch protection rules:

### `main` branch
- ✅ Require pull request before merging
- ✅ Require approvals (at least 1)
- ✅ Require status checks to pass (Pulumi Preview)
- ✅ Require conversation resolution
- ✅ Do not allow bypassing settings

### `staging` branch
- ✅ Require pull request before merging
- ✅ Require status checks to pass

### `development` and `testing` branches
- Optional: Less strict rules for faster iteration

## Advanced Configuration

### Environment-Specific Secrets

If you need different credentials per environment, use **Environment secrets** instead of repository secrets:

1. Go to **Settings → Environments → {environment name}**
2. Add secrets specific to that environment
3. These override repository-level secrets

### Scheduled Drift Detection

Add a scheduled workflow to detect infrastructure drift:

```yaml
on:
  schedule:
    - cron: '0 8 * * 1'  # Every Monday at 8am
```

### Notifications

Add Slack/Discord notifications on deployment success/failure:

```yaml
- name: Notify Slack
  if: always()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
```

## Contact

For issues or questions about the CI/CD pipeline, contact the DevOps team or open an issue in this repository.
