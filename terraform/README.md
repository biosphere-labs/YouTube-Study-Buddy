# YouTube Study Buddy - Terraform Infrastructure

This directory contains Terraform configuration for deploying YouTube Study Buddy infrastructure on AWS.

## Architecture Overview

The infrastructure includes:
- **API Gateway**: HTTP API for REST endpoints
- **Lambda Functions**: Serverless compute for all API handlers
- **DynamoDB**: NoSQL database for users, videos, notes, and transactions
- **S3**: Object storage for generated notes
- **SQS**: Message queue for asynchronous video processing
- **Cognito**: User authentication and authorization
- **CloudWatch**: Logging and monitoring
- **IAM**: Roles and policies for secure access

## Prerequisites

1. **AWS Account**: Active AWS account with appropriate permissions
2. **AWS CLI**: Installed and configured (`aws configure`)
3. **Terraform**: Version 1.0 or later
4. **Python 3.13**: For Lambda function packaging
5. **UV**: Python package manager (for building Lambda layers)

## Initial Setup

### 1. Create Terraform Backend Resources

Before using Terraform, create the S3 bucket and DynamoDB table for state management:

```bash
# Create S3 bucket for Terraform state
aws s3api create-bucket \
  --bucket ytstudybuddy-terraform-state \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket ytstudybuddy-terraform-state \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket ytstudybuddy-terraform-state \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name ytstudybuddy-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### 2. Configure Variables

```bash
# Copy example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
vim terraform.tfvars
```

Required variables:
- `claude_api_key`: Your Anthropic API key
- `stripe_secret_key`: Stripe secret key
- `stripe_publishable_key`: Stripe publishable key
- `stripe_webhook_secret`: Stripe webhook signing secret

### 3. Build Lambda Functions

Before deploying, you need to package Lambda functions:

```bash
# TODO: Create build script
./scripts/build_lambda_functions.sh
```

Each Lambda function should be packaged as a ZIP file in `lambda_functions/`.

### 4. Build Lambda Layer

Package the YouTube Study Buddy CLI as a Lambda layer:

```bash
# TODO: Create build script
./scripts/build_lambda_layer.sh
```

## Deployment

### Initialize Terraform

```bash
terraform init
```

### Select Workspace (Environment)

```bash
# Create/select workspace for environment
terraform workspace new dev
terraform workspace select dev

# For other environments
terraform workspace new staging
terraform workspace new prod
```

### Plan Changes

```bash
# Review planned changes
terraform plan -var-file="terraform.tfvars"

# Save plan to file
terraform plan -var-file="terraform.tfvars" -out=tfplan
```

### Apply Changes

```bash
# Apply from saved plan
terraform apply tfplan

# Or apply directly (will prompt for confirmation)
terraform apply -var-file="terraform.tfvars"
```

## Environment Management

### Development Environment

```bash
terraform workspace select dev
terraform apply -var="environment=dev" -var-file="terraform.tfvars"
```

### Staging Environment

```bash
terraform workspace select staging
terraform apply -var="environment=staging" -var-file="terraform.tfvars"
```

### Production Environment

```bash
terraform workspace select prod
terraform apply -var="environment=prod" -var-file="terraform.tfvars"
```

## Post-Deployment Configuration

### 1. Configure Stripe Webhook

After deployment, configure the Stripe webhook:

```bash
# Get the webhook URL from Terraform outputs
terraform output stripe_webhook_url

# Add this URL to your Stripe dashboard:
# https://dashboard.stripe.com/webhooks
```

### 2. Configure OAuth Providers

If using OAuth providers, configure callback URLs in each provider's console:

```bash
# Get Cognito callback URL
terraform output cognito_domain
```

Add callback URLs:
- Google: https://console.cloud.google.com/apis/credentials
- GitHub: https://github.com/settings/developers
- Discord: https://discord.com/developers/applications

### 3. Update Frontend Configuration

Export configuration for frontend applications:

```bash
# Get all frontend config values
terraform output -json frontend_config > ../frontend_config.json
```

## Useful Commands

### View Current State

```bash
# List all resources
terraform state list

# Show specific resource
terraform state show aws_apigatewayv2_api.main
```

### View Outputs

```bash
# All outputs
terraform output

# Specific output
terraform output api_gateway_url

# JSON format
terraform output -json frontend_config
```

### Import Existing Resources

```bash
# Import existing resource
terraform import aws_s3_bucket.notes ytstudybuddy-dev-notes
```

### Destroy Infrastructure

```bash
# DANGER: This will destroy all resources
terraform destroy -var-file="terraform.tfvars"

# Destroy specific resource
terraform destroy -target=aws_lambda_function.videos_process
```

## Troubleshooting

### Lambda Function Deployment Issues

If Lambda functions fail to deploy:

```bash
# Rebuild Lambda packages
./scripts/build_lambda_functions.sh

# Force recreate Lambda functions
terraform taint aws_lambda_function.videos_process
terraform apply
```

### State Lock Issues

If state is locked:

```bash
# Force unlock (use with caution)
terraform force-unlock LOCK_ID
```

### Permission Issues

Ensure your AWS credentials have the following permissions:
- IAM: Create/manage roles and policies
- Lambda: Create/manage functions
- API Gateway: Create/manage APIs
- DynamoDB: Create/manage tables
- S3: Create/manage buckets
- Cognito: Create/manage user pools
- CloudWatch: Create/manage log groups
- SQS: Create/manage queues

## Monitoring

### CloudWatch Dashboards

Access CloudWatch dashboards in AWS Console:
- Lambda function logs: `/aws/lambda/ytstudybuddy-{env}-*`
- API Gateway logs: `/aws/apigateway/ytstudybuddy-{env}`

### Alarms

Terraform creates CloudWatch alarms for:
- Lambda errors and throttles
- API Gateway 5XX errors
- DynamoDB throttles
- SQS dead letter queue messages

### Cost Monitoring

Check AWS Cost Explorer or set up billing alarms:

```bash
# Budget alert is created for production environment
terraform output deployment_info
```

## Best Practices

1. **Use workspaces**: Separate environments (dev/staging/prod)
2. **Version control**: Commit infrastructure code, not state files
3. **Plan before apply**: Always review changes with `terraform plan`
4. **Use variables**: Keep sensitive data in `terraform.tfvars` (gitignored)
5. **Tag resources**: All resources are tagged with environment and project
6. **Enable logging**: CloudWatch logging enabled by default
7. **State locking**: DynamoDB table prevents concurrent modifications
8. **Backup state**: S3 versioning enabled for state file recovery

## File Structure

```
terraform/
├── backend.tf              # Terraform backend configuration
├── variables.tf            # Input variable definitions
├── locals.tf               # Local values and computed variables
├── main.tf                 # Main infrastructure resources
├── dynamodb.tf             # DynamoDB table definitions
├── s3.tf                   # S3 bucket configuration
├── sqs.tf                  # SQS queue configuration
├── cognito.tf              # Cognito authentication
├── iam.tf                  # IAM roles and policies
├── lambda.tf               # Lambda function definitions
├── api_gateway.tf          # API Gateway configuration
├── outputs.tf              # Output values
├── terraform.tfvars.example # Example variables file
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Security Considerations

1. **Secrets Management**: Sensitive values stored in `terraform.tfvars` (gitignored)
2. **IAM Roles**: Least privilege principle for all Lambda functions
3. **Encryption**: All data encrypted at rest (DynamoDB, S3, SQS)
4. **API Authorization**: Cognito JWT authorizer for protected endpoints
5. **CORS**: Configured for specific domains in production
6. **Logging**: All API calls and Lambda executions logged
7. **MFA**: Optional MFA enabled for Cognito users

## Support

For issues or questions:
1. Check CloudWatch logs for error details
2. Review Terraform plan output before applying
3. Consult AWS documentation for service-specific issues
4. Check project repository issues

## References

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Lambda](https://docs.aws.amazon.com/lambda/)
- [API Gateway](https://docs.aws.amazon.com/apigateway/)
- [DynamoDB](https://docs.aws.amazon.com/dynamodb/)
- [Cognito](https://docs.aws.amazon.com/cognito/)
