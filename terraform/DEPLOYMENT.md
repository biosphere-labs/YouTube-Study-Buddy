# YouTube Study Buddy - Deployment Guide

This guide walks you through deploying YouTube Study Buddy to AWS using Terraform.

## Prerequisites Checklist

- [ ] AWS account with admin access
- [ ] AWS CLI installed and configured
- [ ] Terraform >= 1.0 installed
- [ ] Python 3.13 installed
- [ ] UV package manager installed
- [ ] Claude API key from Anthropic
- [ ] Stripe account with API keys

## Step-by-Step Deployment

### 1. AWS Account Setup

```bash
# Configure AWS credentials
aws configure

# Verify access
aws sts get-caller-identity
```

### 2. Create Backend Resources

```bash
# Run the backend setup script
cd terraform
./scripts/setup_backend.sh
```

Or manually:

```bash
# Create S3 bucket
aws s3api create-bucket \
  --bucket ytstudybuddy-terraform-state \
  --region us-east-1

aws s3api put-bucket-versioning \
  --bucket ytstudybuddy-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table
aws dynamodb create-table \
  --table-name ytstudybuddy-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### 3. Configure Variables

```bash
# Copy example file
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

Required values:
```hcl
claude_api_key         = "sk-ant-xxxxx"
stripe_secret_key      = "sk_test_xxxxx"
stripe_publishable_key = "pk_test_xxxxx"
stripe_webhook_secret  = "whsec_xxxxx"
```

### 4. Build Lambda Packages

```bash
# Build Lambda layer (CLI dependencies)
./scripts/build_lambda_layer.sh

# Build Lambda functions
./scripts/build_lambda_functions.sh
```

### 5. Initialize Terraform

```bash
# Initialize
terraform init

# Create development workspace
terraform workspace new dev
terraform workspace select dev
```

### 6. Deploy Infrastructure

```bash
# Review changes
terraform plan -var-file="terraform.tfvars"

# Deploy (you'll be prompted to confirm)
terraform apply -var-file="terraform.tfvars"
```

This will take 5-10 minutes to complete.

### 7. Configure Post-Deployment

#### A. Stripe Webhook

```bash
# Get webhook URL
terraform output stripe_webhook_url
```

1. Go to https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. Paste the webhook URL
4. Select events: `checkout.session.completed`, `payment_intent.succeeded`
5. Copy the signing secret
6. Update `terraform.tfvars` with the new secret
7. Run `terraform apply` again

#### B. OAuth Providers (Optional)

If using OAuth:

```bash
# Get Cognito domain
terraform output cognito_domain
```

Configure callback URLs in each provider:
- **Callback URL**: `https://{cognito-domain}/oauth2/idpresponse`
- **Logout URL**: `https://{cognito-domain}/logout`

Update `terraform.tfvars` with OAuth credentials and run `terraform apply`.

#### C. Frontend Configuration

```bash
# Export config for frontend
terraform output -json frontend_config > ../frontend_config.json
```

Use these values in your frontend application.

### 8. Verify Deployment

```bash
# Get API URL
API_URL=$(terraform output -raw api_gateway_url)

# Test health endpoint (once implemented)
curl $API_URL/health

# Check CloudWatch logs
aws logs tail /aws/lambda/ytstudybuddy-dev-auth-register --follow
```

## Environment Management

### Development

```bash
terraform workspace select dev
terraform apply -var="environment=dev" -var-file="terraform.tfvars"
```

### Staging

```bash
terraform workspace new staging
terraform workspace select staging
terraform apply -var="environment=staging" -var-file="terraform.tfvars"
```

### Production

```bash
terraform workspace new prod
terraform workspace select prod
terraform apply -var="environment=prod" -var-file="terraform.tfvars.prod"
```

## Updating Infrastructure

### Update Lambda Functions

```bash
# Rebuild functions
./scripts/build_lambda_functions.sh

# Deploy updates
terraform apply -var-file="terraform.tfvars"
```

### Update Lambda Layer

```bash
# Rebuild layer
./scripts/build_lambda_layer.sh

# Deploy (this will trigger Lambda function updates)
terraform apply -var-file="terraform.tfvars"
```

### Update Configuration

```bash
# Edit variables
nano terraform.tfvars

# Apply changes
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

## Rollback

If you need to rollback:

```bash
# View state history
terraform state list

# Rollback to previous state (use S3 versioning)
aws s3api list-object-versions \
  --bucket ytstudybuddy-terraform-state \
  --prefix terraform.tfstate

# Restore previous version
aws s3api get-object \
  --bucket ytstudybuddy-terraform-state \
  --key terraform.tfstate \
  --version-id VERSION_ID \
  terraform.tfstate
```

## Monitoring

### CloudWatch Logs

```bash
# Lambda logs
aws logs tail /aws/lambda/ytstudybuddy-dev-videos-process --follow

# API Gateway logs
aws logs tail /aws/apigateway/ytstudybuddy-dev --follow
```

### CloudWatch Alarms

```bash
# List alarms
aws cloudwatch describe-alarms --alarm-name-prefix ytstudybuddy-dev

# Check alarm status
aws cloudwatch describe-alarms --state-value ALARM
```

### Cost Monitoring

```bash
# View current month costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=TAG,Key=Project
```

## Troubleshooting

### Lambda Function Errors

```bash
# Check recent errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/ytstudybuddy-dev-videos-process \
  --filter-pattern "ERROR"

# Invoke function directly for testing
aws lambda invoke \
  --function-name ytstudybuddy-dev-videos-process \
  --payload '{"test": true}' \
  response.json
```

### API Gateway Issues

```bash
# Test API endpoint
curl -X POST $API_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!@#"}'
```

### DynamoDB Issues

```bash
# Check table status
aws dynamodb describe-table --table-name ytstudybuddy-dev-users

# Query items
aws dynamodb scan --table-name ytstudybuddy-dev-users --limit 5
```

### State Lock Issues

```bash
# Force unlock (use with caution)
terraform force-unlock LOCK_ID
```

## Cleanup

To destroy all resources:

```bash
# Review what will be destroyed
terraform plan -destroy -var-file="terraform.tfvars"

# Destroy (you'll be prompted to confirm)
terraform destroy -var-file="terraform.tfvars"
```

**WARNING**: This will delete all data! Make sure you have backups.

## Security Best Practices

1. **Never commit** `terraform.tfvars` to version control
2. **Enable MFA** on your AWS account
3. **Use separate AWS accounts** for dev/staging/prod
4. **Rotate credentials** regularly
5. **Enable CloudTrail** for audit logs
6. **Review IAM policies** periodically
7. **Use AWS Organizations** for multi-account management
8. **Enable GuardDuty** for threat detection

## Cost Optimization

1. **Use workspaces** to isolate environments
2. **Destroy dev/staging** when not in use
3. **Set DynamoDB** to on-demand billing
4. **Configure S3 lifecycle** policies
5. **Monitor Lambda** concurrent executions
6. **Use Reserved Capacity** for production (if usage is predictable)
7. **Set up billing alerts**

## Support

If you encounter issues:

1. Check CloudWatch logs for error details
2. Review Terraform plan output
3. Verify AWS credentials and permissions
4. Check AWS service limits
5. Consult AWS documentation
6. Check project GitHub issues

## Maintenance Schedule

Recommended schedule:

- **Weekly**: Review CloudWatch alarms and logs
- **Monthly**: Review costs and optimize resources
- **Quarterly**: Update Lambda runtimes and dependencies
- **Annually**: Review IAM policies and access

## Next Steps

After deployment:

1. Implement Lambda function handlers
2. Set up CI/CD pipeline
3. Configure monitoring dashboards
4. Set up automated backups
5. Document API endpoints
6. Create runbooks for common tasks
7. Set up disaster recovery plan
