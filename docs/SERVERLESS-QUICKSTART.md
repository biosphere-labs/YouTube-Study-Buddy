# YouTube Study Buddy - Serverless Quick Start

Get up and running with the serverless architecture in 5-10 minutes.

## Prerequisites

```bash
# Install required tools
pip install awscli aws-sam-cli
brew install terraform  # or download from terraform.io
node --version  # 18.x or higher
python3 --version  # 3.13 or higher
```

## 5-Minute Setup

### 1. Configure AWS

```bash
aws configure
# Enter your AWS credentials when prompted
```

### 2. Clone and Setup

```bash
git clone https://github.com/yourusername/ytstudybuddy.git
cd ytstudybuddy

# Create environment file
cp .env.example .env.dev

# Edit .env.dev and add your keys:
# - CLAUDE_API_KEY
# - STRIPE_SECRET_KEY
# (Optional: OAuth credentials)
```

### 3. Deploy

```bash
# Deploy everything
ENVIRONMENT=dev make deploy-all
```

That's it! The script will:
- Build Lambda layer (2-3 min)
- Deploy infrastructure (3-4 min)
- Deploy Lambda functions (2-3 min)
- Deploy frontend (1-2 min)
- Run smoke tests

**Total time: 8-12 minutes**

### 4. Verify

```bash
# Check deployment
make status

# Seed test data
make seed

# Access the app
# URL will be shown in deployment output
```

## Common Commands

### Deployment

```bash
# Deploy everything
make deploy ENVIRONMENT=dev

# Deploy specific components
make deploy-infra ENVIRONMENT=dev
make deploy-lambda ENVIRONMENT=dev
make deploy-frontend ENVIRONMENT=dev

# Quick deploy to dev
make deploy-dev
```

### Local Development

```bash
# Start local environment
make local

# This starts:
# - DynamoDB Local (port 8000)
# - SAM Local API (port 3001)

# In another terminal, seed data:
ENVIRONMENT=local make seed

# Test locally:
curl http://localhost:3001/videos
```

### Testing

```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration
make test-e2e

# Test Lambda invocations
make test-invoke ENVIRONMENT=dev
```

### Monitoring

```bash
# Tail logs for a function
make logs FUNCTION=submit_video ENVIRONMENT=dev

# View all recent logs
make logs-all ENVIRONMENT=dev

# View metrics
make metrics FUNCTION=submit_video ENVIRONMENT=dev
```

### Data Management

```bash
# Seed development data
make seed ENVIRONMENT=dev

# Clean seed data
make seed-clean ENVIRONMENT=dev
```

### Terraform

```bash
# Plan changes
make tf-plan ENVIRONMENT=dev

# View state
make tf-state ENVIRONMENT=dev

# Save outputs
make tf-outputs ENVIRONMENT=dev

# Format files
make tf-fmt
```

### Rollback

```bash
# Interactive rollback menu
make rollback ENVIRONMENT=dev

# Rollback specific component
make rollback-lambda ENVIRONMENT=dev
make rollback-frontend ENVIRONMENT=dev
```

### Utilities

```bash
# Clean build artifacts
make clean

# Check deployment status
make status ENVIRONMENT=dev

# Show tool versions
make version

# Validate environment
make validate-env ENVIRONMENT=dev
```

## Project Structure

```
ytstudybuddy/
├── lambda/                  # Lambda function code
│   ├── submit_video/       # Submit video endpoint
│   ├── process_video/      # Video processing worker
│   ├── get_video/          # Get video status
│   ├── list_videos/        # List user videos
│   ├── get_note/           # Get note by ID
│   ├── purchase_credits/   # Credit purchase
│   ├── stripe_webhook/     # Stripe webhook handler
│   └── shared/             # Shared utilities
├── lambda-layer/           # Lambda layer (CLI)
│   └── build.sh           # Build script
├── terraform/             # Infrastructure as Code
│   ├── backend.tf         # Terraform backend
│   ├── locals.tf          # Local variables
│   └── variables.tf       # Input variables
├── scripts/               # Deployment scripts
│   ├── deploy-all.sh      # Master deployment
│   ├── deploy-lambda.sh   # Lambda deployment
│   ├── deploy-infrastructure.sh
│   ├── deploy-frontend.sh
│   ├── local-dev.sh       # Local development
│   ├── test-lambda.sh     # Testing
│   ├── rollback.sh        # Rollback
│   └── seed-data.sh       # Seed data
├── webapp/                # Frontend code
│   └── webapp/frontend/   # React app
├── docs/                  # Documentation
└── Makefile              # Convenient commands
```

## Environment Variables

### Required

```bash
# AWS
AWS_REGION=us-east-1
ENVIRONMENT=dev

# API Keys
CLAUDE_API_KEY=sk-ant-your-key
STRIPE_SECRET_KEY=sk_test_your-key
STRIPE_PUBLISHABLE_KEY=pk_test_your-key
```

### Optional

```bash
# OAuth (for social login)
GOOGLE_CLIENT_ID=your-id
GOOGLE_CLIENT_SECRET=your-secret
GITHUB_CLIENT_ID=your-id
GITHUB_CLIENT_SECRET=your-secret
DISCORD_CLIENT_ID=your-id
DISCORD_CLIENT_SECRET=your-secret

# Frontend Deployment
DEPLOY_TARGET=s3  # or vercel, netlify
S3_FRONTEND_BUCKET=ytstudybuddy-frontend-dev
CLOUDFRONT_DISTRIBUTION_ID=E1234567890ABC

# Local Development
LOCAL_PORT=3001
LOCAL_DYNAMO_PORT=8000
DYNAMODB_ENDPOINT=http://localhost:8000
```

## Deployment Targets

### Development

```bash
ENVIRONMENT=dev make deploy-all
```

- Uses `dev` suffix for all resources
- Cheaper configurations (PAY_PER_REQUEST)
- Shorter retention periods
- Test data seeding enabled

### Staging

```bash
ENVIRONMENT=staging make deploy-all
```

- Uses `staging` suffix
- Production-like settings
- Used for testing before prod

### Production

```bash
ENVIRONMENT=production make deploy-all
```

- Requires confirmation
- Production configurations
- Higher availability settings
- Longer retention periods

## Lambda Functions

### submit_video

Submit a video for processing.

**Endpoint**: `POST /videos/submit`

**Payload**:
```json
{
  "youtube_url": "https://www.youtube.com/watch?v=...",
  "subject": "Computer Science"
}
```

**Response**:
```json
{
  "video_id": "uuid",
  "status": "queued"
}
```

### get_video

Get video processing status.

**Endpoint**: `GET /videos/{video_id}`

**Response**:
```json
{
  "video_id": "uuid",
  "status": "processing",
  "progress": 45,
  "current_step": "Generating notes..."
}
```

### get_note

Get generated note.

**Endpoint**: `GET /notes/{note_id}`

**Response**:
```json
{
  "note_id": "uuid",
  "title": "Notes: Video Title",
  "content": "# Markdown content...",
  "created_at": "2024-01-01T00:00:00Z"
}
```

## Testing Locally

### Start Local Environment

```bash
# Terminal 1: Start services
make local

# Terminal 2: Seed data
ENVIRONMENT=local make seed

# Terminal 3: Test API
curl http://localhost:3001/videos
```

### Test Lambda Function

```bash
# Create test event
cat > test-event.json <<EOF
{
  "body": "{\"youtube_url\":\"https://www.youtube.com/watch?v=dQw4w9WgXcQ\"}",
  "requestContext": {
    "authorizer": {
      "claims": {
        "sub": "test-user-123"
      }
    }
  }
}
EOF

# Test locally with SAM
sam local invoke SubmitVideoFunction --event test-event.json
```

## Troubleshooting

### Lambda Timeout

```bash
# Check function logs
make logs FUNCTION=process_video ENVIRONMENT=dev

# Check timeout setting
aws lambda get-function-configuration \
  --function-name ytstudy-dev-process_video \
  --query 'Timeout'
```

### DynamoDB Access Denied

```bash
# Check IAM role permissions
aws iam get-role-policy \
  --role-name ytstudy-lambda-execution-role \
  --policy-name dynamodb-access
```

### Frontend Can't Access API

```bash
# Check CORS settings in API Gateway
# Update in Terraform or AWS Console

# Verify API Gateway URL in frontend env
cat webapp/webapp/frontend/.env.production
```

### Cold Start Issues

```bash
# Enable provisioned concurrency (production only)
aws lambda put-provisioned-concurrency-config \
  --function-name ytstudy-prod-submit_video \
  --provisioned-concurrent-executions 1
```

## Cost Optimization

### Development

```bash
# Use on-demand billing (already configured)
# Stop local services when not in use
make local-stop
```

### Production

```bash
# Set up billing alerts
aws cloudwatch put-metric-alarm \
  --alarm-name ytstudy-prod-billing \
  --threshold 50 \
  --comparison-operator GreaterThanThreshold

# Review costs monthly
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY
```

## CI/CD

### GitHub Actions

```bash
# Workflow file already created at:
.github/workflows/deploy.yml

# Configure GitHub Secrets:
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY
# - CLAUDE_API_KEY
# - STRIPE_SECRET_KEY
```

### Manual Deployment

```bash
# Build and test locally
make build
make test

# Deploy to staging
ENVIRONMENT=staging make deploy-all

# Test staging
ENVIRONMENT=staging make test-e2e

# Deploy to production (requires approval)
ENVIRONMENT=production make deploy-all
```

## Useful Resources

- **Full Deployment Guide**: [SERVERLESS-DEPLOYMENT.md](./SERVERLESS-DEPLOYMENT.md)
- **Architecture**: [SERVERLESS-LAMBDA-ARCHITECTURE.md](./SERVERLESS-LAMBDA-ARCHITECTURE.md)
- **Makefile Help**: `make help`
- **AWS Lambda Docs**: https://docs.aws.amazon.com/lambda/
- **Terraform AWS Provider**: https://registry.terraform.io/providers/hashicorp/aws/

## Quick Reference

```bash
# Build
make build                           # Build Lambda layer + package functions
make build-layer                     # Build Lambda layer only

# Deploy
make deploy                          # Deploy all (infrastructure + Lambda + frontend)
make deploy-dev                      # Quick deploy to dev
make deploy-staging                  # Deploy to staging
make deploy-production               # Deploy to production (requires confirmation)

# Test
make test                            # Run all tests
make test-unit                       # Unit tests only
make test-e2e                        # End-to-end tests

# Local
make local                           # Start local environment
make local-stop                      # Stop local services

# Data
make seed                            # Seed development data
make seed-clean                      # Clean seed data

# Monitor
make logs FUNCTION=name              # Tail function logs
make logs-all                        # Show all recent logs
make status                          # Show deployment status

# Rollback
make rollback                        # Interactive rollback
make rollback-lambda                 # Rollback Lambda functions
make rollback-all                    # Rollback everything

# Utilities
make clean                           # Clean build artifacts
make version                         # Show tool versions
make help                            # Show all commands
```

## Getting Help

```bash
# Show Makefile help
make help

# View documentation
make docs

# Check deployment status
make status
```

## Next Steps

1. ✅ Complete deployment
2. ✅ Seed test data
3. ✅ Test the application
4. Configure OAuth providers
5. Set up Stripe webhook
6. Enable monitoring and alerts
7. Configure CI/CD
8. Deploy to staging
9. Deploy to production

For detailed instructions, see [SERVERLESS-DEPLOYMENT.md](./SERVERLESS-DEPLOYMENT.md)
