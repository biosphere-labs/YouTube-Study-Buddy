# Output values for YouTube Study Buddy infrastructure

# API Gateway outputs
output "api_gateway_url" {
  description = "URL of the API Gateway"
  value       = aws_apigatewayv2_stage.main.invoke_url
}

output "api_gateway_id" {
  description = "ID of the API Gateway"
  value       = aws_apigatewayv2_api.main.id
}

output "api_gateway_execution_arn" {
  description = "Execution ARN of the API Gateway"
  value       = aws_apigatewayv2_api.main.execution_arn
}

# Cognito outputs
output "cognito_user_pool_id" {
  description = "ID of the Cognito User Pool"
  value       = aws_cognito_user_pool.main.id
}

output "cognito_user_pool_arn" {
  description = "ARN of the Cognito User Pool"
  value       = aws_cognito_user_pool.main.arn
}

output "cognito_user_pool_endpoint" {
  description = "Endpoint of the Cognito User Pool"
  value       = aws_cognito_user_pool.main.endpoint
}

output "cognito_client_id" {
  description = "ID of the Cognito User Pool Client"
  value       = aws_cognito_user_pool_client.main.id
  sensitive   = true
}

output "cognito_identity_pool_id" {
  description = "ID of the Cognito Identity Pool"
  value       = aws_cognito_identity_pool.main.id
}

output "cognito_domain" {
  description = "Cognito hosted UI domain"
  value       = var.cognito_domain_prefix != "" ? "https://${var.cognito_domain_prefix}.auth.${var.aws_region}.amazoncognito.com" : null
}

# DynamoDB outputs
output "dynamodb_table_names" {
  description = "Names of all DynamoDB tables"
  value = {
    users               = aws_dynamodb_table.users.name
    videos              = aws_dynamodb_table.videos.name
    notes               = aws_dynamodb_table.notes.name
    credit_transactions = aws_dynamodb_table.credit_transactions.name
  }
}

output "dynamodb_table_arns" {
  description = "ARNs of all DynamoDB tables"
  value = {
    users               = aws_dynamodb_table.users.arn
    videos              = aws_dynamodb_table.videos.arn
    notes               = aws_dynamodb_table.notes.arn
    credit_transactions = aws_dynamodb_table.credit_transactions.arn
  }
}

# S3 outputs
output "notes_bucket_name" {
  description = "Name of the S3 bucket for notes"
  value       = aws_s3_bucket.notes.id
}

output "notes_bucket_arn" {
  description = "ARN of the S3 bucket for notes"
  value       = aws_s3_bucket.notes.arn
}

output "notes_bucket_domain_name" {
  description = "Domain name of the S3 bucket for notes"
  value       = aws_s3_bucket.notes.bucket_domain_name
}

# SQS outputs
output "video_processing_queue_url" {
  description = "URL of the video processing SQS queue"
  value       = aws_sqs_queue.video_processing.url
}

output "video_processing_queue_arn" {
  description = "ARN of the video processing SQS queue"
  value       = aws_sqs_queue.video_processing.arn
}

output "video_processing_dlq_url" {
  description = "URL of the video processing dead letter queue"
  value       = aws_sqs_queue.video_processing_dlq.url
}

# Lambda outputs
output "lambda_function_names" {
  description = "Names of all Lambda functions"
  value       = local.lambda_functions
}

output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_execution.arn
}

output "lambda_layer_arn" {
  description = "ARN of the CLI Lambda layer"
  value       = aws_lambda_layer_version.cli.arn
}

# CloudWatch outputs
output "cloudwatch_log_groups" {
  description = "CloudWatch log groups"
  value = {
    api_gateway = aws_cloudwatch_log_group.api_gateway.name
    lambda      = [for k, v in aws_cloudwatch_log_group.lambda_logs : v.name]
  }
}

# IAM outputs
output "lambda_execution_role_name" {
  description = "Name of the Lambda execution role"
  value       = aws_iam_role.lambda_execution.name
}

# Environment outputs
output "environment" {
  description = "Deployment environment"
  value       = var.environment
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "aws_account_id" {
  description = "AWS account ID"
  value       = data.aws_caller_identity.current.account_id
}

# Application configuration outputs (for frontend)
output "frontend_config" {
  description = "Configuration values for frontend application"
  value = {
    api_url              = aws_apigatewayv2_stage.main.invoke_url
    cognito_user_pool_id = aws_cognito_user_pool.main.id
    cognito_client_id    = aws_cognito_user_pool_client.main.id
    cognito_region       = var.aws_region
    cognito_domain       = var.cognito_domain_prefix != "" ? "${var.cognito_domain_prefix}.auth.${var.aws_region}.amazoncognito.com" : null
    identity_pool_id     = aws_cognito_identity_pool.main.id
  }
  sensitive = true
}

# Webhook URL for Stripe
output "stripe_webhook_url" {
  description = "Stripe webhook URL"
  value       = "${aws_apigatewayv2_stage.main.invoke_url}/webhooks/stripe"
}

# SSM Parameter names
output "ssm_parameters" {
  description = "SSM Parameter Store parameter names"
  value = {
    api_url             = aws_ssm_parameter.api_url.name
    cognito_user_pool_id = aws_ssm_parameter.cognito_user_pool_id.name
    cognito_client_id   = aws_ssm_parameter.cognito_client_id.name
    notes_bucket        = aws_ssm_parameter.notes_bucket.name
    video_queue_url     = aws_ssm_parameter.video_queue_url.name
  }
}

# Complete deployment information
output "deployment_info" {
  description = "Complete deployment information"
  value = {
    environment         = var.environment
    region              = var.aws_region
    api_url             = aws_apigatewayv2_stage.main.invoke_url
    stripe_webhook_url  = "${aws_apigatewayv2_stage.main.invoke_url}/webhooks/stripe"
    notes_bucket        = aws_s3_bucket.notes.id
    queue_url           = aws_sqs_queue.video_processing.url
  }
}
