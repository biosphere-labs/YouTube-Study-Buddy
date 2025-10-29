# YouTube Study Buddy - Serverless Deployment Guide

Complete guide for deploying the YouTube Study Buddy serverless architecture using AWS Lambda, DynamoDB, and S3.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [Initial Setup](#initial-setup)
- [Configuration](#configuration)
- [Deployment Steps](#deployment-steps)
- [Post-Deployment](#post-deployment)
- [Monitoring and Logging](#monitoring-and-logging)
- [Troubleshooting](#troubleshooting)
- [Cost Management](#cost-management)

## Prerequisites

### Required Tools

Install the following tools before deployment:

```bash
# AWS CLI
pip install awscli
aws --version  # Should be 2.x or higher

# Terraform
# Download from https://www.terraform.io/downloads
terraform --version  # Should be 1.0 or higher

# Node.js and npm (for frontend)
node --version  # Should be 18.x or higher
npm --version   # Should be 9.x or higher

# Python (for Lambda functions)
python3 --version  # Should be 3.13 or higher
pip3 --version

# Optional: SAM CLI (for local development)
pip install aws-sam-cli
```

### AWS Account Setup

1. **Create AWS Account** (if you don't have one):
   - Go to https://aws.amazon.com/
   - Sign up for an account
   - Add billing information

2. **Create IAM User** with appropriate permissions:
   ```bash
   # Required permissions:
   # - Lambda full access
   # - DynamoDB full access
   # - S3 full access
   # - CloudWatch Logs
   # - API Gateway
   # - Cognito
   # - IAM (for creating roles)
   ```

3. **Configure AWS CLI**:
   ```bash
   aws configure
   # AWS Access Key ID: [your-access-key]
   # AWS Secret Access Key: [your-secret-key]
   # Default region: us-east-1
   # Default output format: json
   ```

4. **Verify Configuration**:
   ```bash
   aws sts get-caller-identity
   # Should show your account ID and user ARN
   ```

### API Keys and Secrets

Obtain the following before deployment:

1. **Claude API Key**:
   - Sign up at https://console.anthropic.com/
   - Generate an API key
   - Store securely

2. **Stripe Keys** (for payments):
   - Create account at https://stripe.com/
   - Get publishable and secret keys
   - Set up webhook endpoint (will configure later)

3. **OAuth Providers** (Google/GitHub/Discord):
   - Create OAuth applications for each provider
   - Collect client IDs and secrets
   - Configure callback URLs (will set after deployment)

## Architecture Overview

```
Frontend (React) → API Gateway → Lambda Functions → DynamoDB
                                       ↓
                                   S3 (Notes)
                                       ↓
                                 SQS (Queue)
```

### Components:

- **API Gateway**: HTTP API for all endpoints
- **Lambda Functions**:
  - `submit_video`: Accept video submissions
  - `process_video`: Process videos with CLI
  - `get_video`: Retrieve video status
  - `list_videos`: List user's videos
  - `get_note`: Retrieve notes
  - `purchase_credits`: Handle credit purchases
  - `stripe_webhook`: Process Stripe webhooks
- **DynamoDB Tables**:
  - `ytstudy-users-{env}`: User accounts
  - `ytstudy-videos-{env}`: Video processing records
  - `ytstudy-notes-{env}`: Generated notes
- **S3 Buckets**:
  - `ytstudy-notes-{env}`: Note storage
  - `ytstudy-frontend-{env}`: Frontend hosting (optional)
- **SQS Queue**: Video processing queue
- **Cognito**: User authentication

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/ytstudybuddy.git
cd ytstudybuddy
```

### 2. Create Environment Files

Create `.env.dev` for development:

```bash
# AWS Configuration
AWS_REGION=us-east-1
ENVIRONMENT=dev

# API Keys
CLAUDE_API_KEY=sk-ant-your-key-here
STRIPE_SECRET_KEY=sk_test_your-key-here
STRIPE_PUBLISHABLE_KEY=pk_test_your-key-here

# OAuth Providers
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
DISCORD_CLIENT_ID=your-discord-client-id
DISCORD_CLIENT_SECRET=your-discord-client-secret

# Frontend
DEPLOY_TARGET=s3
```

Create similar files for staging and production:
- `.env.staging`
- `.env.production`

### 3. Initialize Terraform Backend

Create S3 bucket for Terraform state:

```bash
# Create state bucket
aws s3 mb s3://ytstudybuddy-terraform-state --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket ytstudybuddy-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name ytstudybuddy-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

## Configuration

### Terraform Variables

Create `terraform/environments/dev.tfvars`:

```hcl
environment = "dev"
aws_region  = "us-east-1"

# DynamoDB
dynamodb_billing_mode = "PAY_PER_REQUEST"

# Lambda
lambda_timeout     = 900  # 15 minutes
lambda_memory_size = 2048

# S3
enable_s3_versioning = true

# Cognito
cognito_password_policy = {
  minimum_length    = 8
  require_lowercase = true
  require_numbers   = true
  require_symbols   = false
  require_uppercase = true
}

# Tags
tags = {
  Project     = "YouTubeStudyBuddy"
  Environment = "dev"
  ManagedBy   = "Terraform"
}
```

## Deployment Steps

### Quick Deployment (Recommended)

Use the master deployment script:

```bash
# Deploy everything to dev environment
ENVIRONMENT=dev make deploy-all

# Or with script directly
ENVIRONMENT=dev ./scripts/deploy-all.sh
```

This will:
1. Build Lambda layer
2. Deploy infrastructure (Terraform)
3. Deploy Lambda functions
4. Deploy frontend
5. Run smoke tests
6. Show deployment summary

### Step-by-Step Deployment

If you prefer more control:

#### 1. Build Lambda Layer

```bash
make build-layer

# Or manually:
cd lambda-layer
bash build.sh
```

This creates `cli-layer.zip` with the Python CLI and all dependencies.

#### 2. Deploy Infrastructure

```bash
# Initialize Terraform
ENVIRONMENT=dev make tf-init

# Validate configuration
ENVIRONMENT=dev make tf-validate

# Plan changes
ENVIRONMENT=dev make tf-plan

# Deploy
ENVIRONMENT=dev make deploy-infra
```

Terraform will create:
- DynamoDB tables
- S3 buckets
- SQS queue
- IAM roles and policies
- API Gateway
- Cognito User Pool
- Lambda function stubs

#### 3. Deploy Lambda Functions

```bash
ENVIRONMENT=dev make deploy-lambda

# Or deploy specific function:
ENVIRONMENT=dev ./scripts/deploy-lambda.sh submit_video
```

This:
- Packages each Lambda function
- Uploads to S3 (if > 50MB)
- Updates Lambda function code
- Updates environment variables
- Tests each function

#### 4. Deploy Frontend

```bash
# Deploy to S3 + CloudFront
ENVIRONMENT=production DEPLOY_TARGET=s3 make deploy-frontend

# Or deploy to Vercel
ENVIRONMENT=production DEPLOY_TARGET=vercel make deploy-frontend

# Or deploy to Netlify
ENVIRONMENT=production DEPLOY_TARGET=netlify make deploy-frontend
```

## Post-Deployment

### 1. Configure OAuth Providers

After deployment, you'll have an API Gateway URL. Configure OAuth callback URLs:

**Google OAuth:**
1. Go to Google Cloud Console
2. Navigate to APIs & Services > Credentials
3. Edit your OAuth 2.0 Client
4. Add authorized redirect URI:
   ```
   https://your-api-gateway-url/auth/google/callback
   https://your-frontend-url/auth/callback
   ```

**GitHub OAuth:**
1. Go to GitHub Settings > Developer settings > OAuth Apps
2. Edit your application
3. Set callback URL:
   ```
   https://your-frontend-url/auth/callback
   ```

**Discord OAuth:**
1. Go to Discord Developer Portal
2. Edit your application
3. Add redirect:
   ```
   https://your-frontend-url/auth/callback
   ```

### 2. Configure Stripe Webhook

1. Go to Stripe Dashboard > Developers > Webhooks
2. Add endpoint:
   ```
   https://your-api-gateway-url/webhooks/stripe
   ```
3. Select events:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `charge.refunded`
4. Copy webhook signing secret
5. Update Lambda environment variable:
   ```bash
   aws lambda update-function-configuration \
     --function-name ytstudy-dev-stripe_webhook \
     --environment "Variables={STRIPE_WEBHOOK_SECRET=whsec_your_secret}"
   ```

### 3. Seed Development Data

```bash
ENVIRONMENT=dev make seed
```

This creates:
- Test users in Cognito
- Sample videos in DynamoDB
- Test notes
- Initial credits

Test credentials:
- Email: `test@example.com`
- Password: `TestPassword123!`

### 4. Verify Deployment

Run smoke tests:

```bash
ENVIRONMENT=dev make test-e2e
```

Check deployment status:

```bash
make status
```

Access the frontend:
```bash
# Get frontend URL from outputs
cat .env.dev.terraform | grep FRONTEND_URL
```

## Monitoring and Logging

### CloudWatch Logs

View logs for specific function:

```bash
# Tail logs
make logs FUNCTION=submit_video ENVIRONMENT=dev

# Or with AWS CLI:
aws logs tail /aws/lambda/ytstudy-dev-submit_video --follow
```

View all recent logs:

```bash
make logs-all ENVIRONMENT=dev
```

### CloudWatch Metrics

View metrics for a function:

```bash
make metrics FUNCTION=submit_video ENVIRONMENT=dev
```

Or use CloudWatch Console:
1. Go to CloudWatch > Metrics
2. Select "Lambda" namespace
3. View invocations, errors, duration

### X-Ray Tracing (Optional)

Enable X-Ray for distributed tracing:

```bash
aws lambda update-function-configuration \
  --function-name ytstudy-dev-process_video \
  --tracing-config Mode=Active
```

### CloudWatch Dashboards

Create a dashboard to monitor all functions:

```bash
# Create dashboard JSON
cat > dashboard.json <<EOF
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "AWS/Lambda", "Invocations", { "stat": "Sum" } ],
          [ ".", "Errors", { "stat": "Sum" } ],
          [ ".", "Duration", { "stat": "Average" } ]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "Lambda Metrics"
      }
    }
  ]
}
EOF

# Create dashboard
aws cloudwatch put-dashboard \
  --dashboard-name ytstudy-dev \
  --dashboard-body file://dashboard.json
```

## Troubleshooting

### Common Issues

#### 1. Lambda Function Timeout

**Symptom**: Function times out after 15 minutes

**Solution**:
- Lambda has a 15-minute maximum timeout
- If videos take longer, consider using Step Functions or ECS Fargate
- Optimize CLI processing time

#### 2. Cold Start Latency

**Symptom**: First request is slow (2-5 seconds)

**Solutions**:
```bash
# Enable provisioned concurrency (costs more)
aws lambda put-provisioned-concurrency-config \
  --function-name ytstudy-prod-submit_video \
  --provisioned-concurrent-executions 1
```

Or accept cold starts for dev/staging.

#### 3. DynamoDB Throttling

**Symptom**: `ProvisionedThroughputExceededException`

**Solution**:
- Switch to on-demand billing mode (already configured)
- Or increase provisioned capacity

#### 4. Lambda Package Too Large

**Symptom**: Deployment fails, package > 250MB

**Solution**:
- Package is already optimized
- Ensure Lambda layer is used
- Remove unnecessary dependencies

#### 5. CORS Errors

**Symptom**: Frontend can't access API

**Solution**:
```bash
# Update API Gateway CORS settings in Terraform
# Or manually in AWS Console:
# API Gateway > Your API > CORS
```

### Debug Mode

Enable verbose logging:

```bash
# Update Lambda environment variable
aws lambda update-function-configuration \
  --function-name ytstudy-dev-process_video \
  --environment "Variables={LOG_LEVEL=DEBUG}"
```

### Test Lambda Locally

```bash
# Start local environment
make local

# Test function locally
sam local invoke SubmitVideoFunction \
  --event test-events/submit-video.json
```

## Cost Management

### Estimated Monthly Costs

For 1000 videos/month:

| Service | Cost |
|---------|------|
| Lambda (execution) | $4-5 |
| DynamoDB | $2-5 |
| S3 (storage + transfer) | $1-3 |
| API Gateway | Free (< 1M requests) |
| CloudWatch Logs | $2-5 |
| **Total** | **$10-20/month** |

### Cost Optimization Tips

1. **Use Reserved Capacity** for predictable workloads:
   ```bash
   # For production, consider reserved DynamoDB capacity
   ```

2. **Set up Billing Alerts**:
   ```bash
   aws cloudwatch put-metric-alarm \
     --alarm-name ytstudy-billing-alert \
     --alarm-description "Alert when bill exceeds $50" \
     --metric-name EstimatedCharges \
     --namespace AWS/Billing \
     --statistic Maximum \
     --period 21600 \
     --threshold 50 \
     --comparison-operator GreaterThanThreshold
   ```

3. **Enable S3 Lifecycle Policies**:
   - Move old notes to S3 Glacier after 90 days
   - Delete old CloudWatch logs after 30 days

4. **Clean up unused resources**:
   ```bash
   # List unused Lambda versions
   aws lambda list-versions-by-function \
     --function-name ytstudy-dev-submit_video

   # Delete old versions
   aws lambda delete-function \
     --function-name ytstudy-dev-submit_video:5
   ```

### Monitor Costs

View current costs:
```bash
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics "BlendedCost" \
  --group-by Type=SERVICE
```

## Rollback

If deployment fails or issues occur:

```bash
# Interactive rollback menu
ENVIRONMENT=dev make rollback

# Rollback specific component
make rollback-lambda ENVIRONMENT=dev
make rollback-frontend ENVIRONMENT=dev

# Complete rollback
make rollback-all ENVIRONMENT=dev
```

See [Rollback Documentation](./ROLLBACK.md) for details.

## Security Best Practices

1. **Rotate API Keys** regularly
2. **Use Secrets Manager** for sensitive data:
   ```bash
   aws secretsmanager create-secret \
     --name ytstudy/dev/claude-api-key \
     --secret-string "$CLAUDE_API_KEY"
   ```
3. **Enable encryption** at rest for DynamoDB
4. **Use VPC** for Lambda functions (optional)
5. **Implement rate limiting** on API Gateway
6. **Enable CloudTrail** for audit logging

## Next Steps

- [Quick Start Guide](./SERVERLESS-QUICKSTART.md)
- [CI/CD Setup](./CI-CD.md)
- [Monitoring Guide](./MONITORING.md)
- [API Documentation](./API.md)

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/ytstudybuddy/issues
- Documentation: https://docs.ytstudybuddy.com

---

Last Updated: $(date)
