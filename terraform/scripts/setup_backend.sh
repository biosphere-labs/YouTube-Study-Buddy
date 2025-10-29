#!/bin/bash
# Setup Terraform backend resources in AWS

set -e

BUCKET_NAME="ytstudybuddy-terraform-state"
TABLE_NAME="ytstudybuddy-terraform-locks"
REGION="us-east-1"

echo "Setting up Terraform backend resources..."
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "ERROR: AWS CLI is not configured. Run 'aws configure' first."
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account ID: $ACCOUNT_ID"
echo "Region: $REGION"
echo ""

# Create S3 bucket
echo "Creating S3 bucket: $BUCKET_NAME"
if aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
    echo "  ✓ Bucket already exists"
else
    aws s3api create-bucket \
        --bucket "$BUCKET_NAME" \
        --region "$REGION"
    echo "  ✓ Bucket created"
fi

# Enable versioning
echo "Enabling versioning..."
aws s3api put-bucket-versioning \
    --bucket "$BUCKET_NAME" \
    --versioning-configuration Status=Enabled
echo "  ✓ Versioning enabled"

# Enable encryption
echo "Enabling encryption..."
aws s3api put-bucket-encryption \
    --bucket "$BUCKET_NAME" \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            },
            "BucketKeyEnabled": true
        }]
    }'
echo "  ✓ Encryption enabled"

# Block public access
echo "Blocking public access..."
aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration \
        BlockPublicAcls=true,\
IgnorePublicAcls=true,\
BlockPublicPolicy=true,\
RestrictPublicBuckets=true
echo "  ✓ Public access blocked"

# Create DynamoDB table
echo ""
echo "Creating DynamoDB table: $TABLE_NAME"
if aws dynamodb describe-table --table-name "$TABLE_NAME" --region "$REGION" &>/dev/null; then
    echo "  ✓ Table already exists"
else
    aws dynamodb create-table \
        --table-name "$TABLE_NAME" \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION" \
        --tags Key=Project,Value=ytstudybuddy Key=ManagedBy,Value=terraform
    echo "  ✓ Table created"

    # Wait for table to be active
    echo "  Waiting for table to be active..."
    aws dynamodb wait table-exists --table-name "$TABLE_NAME" --region "$REGION"
    echo "  ✓ Table is active"
fi

# Enable point-in-time recovery
echo "Enabling point-in-time recovery..."
aws dynamodb update-continuous-backups \
    --table-name "$TABLE_NAME" \
    --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true \
    --region "$REGION" || echo "  ! Could not enable PITR (may require additional permissions)"

echo ""
echo "Backend setup complete!"
echo ""
echo "Backend configuration:"
echo "  Bucket: $BUCKET_NAME"
echo "  Table: $TABLE_NAME"
echo "  Region: $REGION"
echo ""
echo "Next steps:"
echo "1. Update backend.tf if you used different names"
echo "2. Copy terraform.tfvars.example to terraform.tfvars"
echo "3. Fill in your API keys and configuration"
echo "4. Run 'terraform init'"
