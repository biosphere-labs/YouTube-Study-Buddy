# Main Terraform configuration for YouTube Study Buddy
# This file serves as the entry point and orchestrates all infrastructure components

# Data sources

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# Get current AWS region
data "aws_region" "current" {}

# Get available availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# CloudWatch Alarms for monitoring

# Lambda error alarm
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = local.lambda_functions

  alarm_name          = "${each.value}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Alert when Lambda function errors exceed threshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = each.value
  }

  tags = local.common_tags
}

# Lambda throttles alarm
resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  for_each = local.lambda_functions

  alarm_name          = "${each.value}-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Alert when Lambda function is throttled"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = each.value
  }

  tags = local.common_tags
}

# API Gateway 5XX errors alarm
resource "aws_cloudwatch_metric_alarm" "api_gateway_5xx" {
  alarm_name          = "${local.name_prefix}-api-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Alert when API Gateway 5XX errors exceed threshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiId = aws_apigatewayv2_api.main.id
  }

  tags = local.common_tags
}

# DynamoDB throttles alarm
resource "aws_cloudwatch_metric_alarm" "dynamodb_throttles" {
  for_each = local.dynamodb_tables

  alarm_name          = "${each.value}-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "UserErrors"
  namespace           = "AWS/DynamoDB"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Alert when DynamoDB throttles occur"
  treat_missing_data  = "notBreaching"

  dimensions = {
    TableName = each.value
  }

  tags = local.common_tags
}

# Budget alert (optional)
resource "aws_budgets_budget" "monthly" {
  count = var.environment == "prod" ? 1 : 0

  name              = "${local.name_prefix}-monthly-budget"
  budget_type       = "COST"
  limit_amount      = "100"
  limit_unit        = "USD"
  time_period_start = "2024-01-01_00:00"
  time_unit         = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = []
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = []
  }
}

# Systems Manager Parameter Store for configuration

# API Gateway URL
resource "aws_ssm_parameter" "api_url" {
  name        = "/${var.project_name}/${var.environment}/api_url"
  description = "API Gateway URL"
  type        = "String"
  value       = aws_apigatewayv2_stage.main.invoke_url

  tags = local.common_tags
}

# Cognito User Pool ID
resource "aws_ssm_parameter" "cognito_user_pool_id" {
  name        = "/${var.project_name}/${var.environment}/cognito_user_pool_id"
  description = "Cognito User Pool ID"
  type        = "String"
  value       = aws_cognito_user_pool.main.id

  tags = local.common_tags
}

# Cognito User Pool Client ID
resource "aws_ssm_parameter" "cognito_client_id" {
  name        = "/${var.project_name}/${var.environment}/cognito_client_id"
  description = "Cognito User Pool Client ID"
  type        = "String"
  value       = aws_cognito_user_pool_client.main.id

  tags = local.common_tags
}

# S3 Notes Bucket
resource "aws_ssm_parameter" "notes_bucket" {
  name        = "/${var.project_name}/${var.environment}/notes_bucket"
  description = "S3 bucket for notes"
  type        = "String"
  value       = aws_s3_bucket.notes.id

  tags = local.common_tags
}

# SQS Queue URL
resource "aws_ssm_parameter" "video_queue_url" {
  name        = "/${var.project_name}/${var.environment}/video_queue_url"
  description = "SQS queue URL for video processing"
  type        = "String"
  value       = aws_sqs_queue.video_processing.url

  tags = local.common_tags
}
