#!/bin/bash
# Login to Pulumi with R2 backend using explicit endpoint

# Source environment
if [ -f .env ]; then
    source .env
fi

# R2 configuration
R2_ACCOUNT_ID="2d45fcd3b3e68735a6ab3542fb494c19"
BUCKET_NAME="clustera-infrastructure-pulumi"

# Build the S3 URL with endpoint parameter (Pulumi format)
S3_URL="s3://${BUCKET_NAME}?endpoint=${R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

echo "Logging in to Pulumi with R2 backend..."
echo "Bucket: ${BUCKET_NAME}"
echo "Endpoint: ${R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
echo ""

# Login with explicit endpoint
pulumi login "${S3_URL}"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully logged in to R2 backend!"
    echo "You can now run: pulumi stack init <stack-name>"
else
    echo ""
    echo "❌ Login failed. Troubleshooting:"
    echo ""
    echo "1. Check if bucket exists:"
    echo "   npx wrangler r2 bucket create ${BUCKET_NAME}"
    echo ""
    echo "2. Verify R2 credentials are set:"
    echo "   echo \$AWS_ACCESS_KEY_ID"
    echo "   echo \$AWS_SECRET_ACCESS_KEY"
    echo ""
    echo "3. Try creating the bucket first, then run this script again"
fi
