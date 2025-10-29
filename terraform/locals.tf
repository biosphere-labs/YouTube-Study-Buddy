locals {
  # Common resource naming
  name_prefix = "${var.project_name}-${var.environment}"

  # Common tags
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      Repository  = "ytstudybuddy"
    },
    var.tags
  )

  # Lambda function names
  lambda_functions = {
    auth_register = "${local.name_prefix}-auth-register"
    auth_login    = "${local.name_prefix}-auth-login"
    auth_refresh  = "${local.name_prefix}-auth-refresh"
    auth_verify   = "${local.name_prefix}-auth-verify"

    videos_submit   = "${local.name_prefix}-videos-submit"
    videos_list     = "${local.name_prefix}-videos-list"
    videos_get      = "${local.name_prefix}-videos-get"
    videos_delete   = "${local.name_prefix}-videos-delete"
    videos_process  = "${local.name_prefix}-videos-process"

    notes_get      = "${local.name_prefix}-notes-get"
    notes_list     = "${local.name_prefix}-notes-list"
    notes_download = "${local.name_prefix}-notes-download"

    credits_get       = "${local.name_prefix}-credits-get"
    credits_history   = "${local.name_prefix}-credits-history"
    credits_checkout  = "${local.name_prefix}-credits-checkout"
    credits_webhook   = "${local.name_prefix}-credits-webhook"

    user_get    = "${local.name_prefix}-user-get"
    user_update = "${local.name_prefix}-user-update"
  }

  # DynamoDB table names
  dynamodb_tables = {
    users               = "${local.name_prefix}-users"
    videos              = "${local.name_prefix}-videos"
    notes               = "${local.name_prefix}-notes"
    credit_transactions = "${local.name_prefix}-credit-transactions"
  }

  # S3 bucket names
  s3_buckets = {
    notes = "${local.name_prefix}-notes"
  }

  # SQS queue names
  sqs_queues = {
    video_processing = "${local.name_prefix}-video-processing"
  }

  # CloudWatch log group names
  log_groups = {
    api_gateway = "/aws/apigateway/${local.name_prefix}"
  }

  # Cognito resource names
  cognito_names = {
    user_pool        = "${local.name_prefix}-users"
    user_pool_client = "${local.name_prefix}-client"
    identity_pool    = "${local.name_prefix}-identity"
  }

  # Lambda layer names
  lambda_layers = {
    cli = "${local.name_prefix}-cli-layer"
  }

  # API Gateway configuration
  api_gateway = {
    name        = "${local.name_prefix}-api"
    stage_name  = var.environment
    description = "YouTube Study Buddy API - ${var.environment}"
  }

  # IAM role names
  iam_roles = {
    lambda_execution = "${local.name_prefix}-lambda-execution"
  }

  # Environment variables for Lambda functions
  lambda_env_vars = {
    ENVIRONMENT             = var.environment
    USERS_TABLE             = aws_dynamodb_table.users.name
    VIDEOS_TABLE            = aws_dynamodb_table.videos.name
    NOTES_TABLE             = aws_dynamodb_table.notes.name
    CREDIT_TRANSACTIONS_TABLE = aws_dynamodb_table.credit_transactions.name
    NOTES_BUCKET            = aws_s3_bucket.notes.id
    VIDEO_PROCESSING_QUEUE  = aws_sqs_queue.video_processing.url
    COGNITO_USER_POOL_ID    = aws_cognito_user_pool.main.id
    COGNITO_CLIENT_ID       = aws_cognito_user_pool_client.main.id
    CLAUDE_API_KEY          = var.claude_api_key
    STRIPE_SECRET_KEY       = var.stripe_secret_key
    STRIPE_WEBHOOK_SECRET   = var.stripe_webhook_secret
    FREE_TIER_CREDITS       = tostring(var.free_tier_credits)
    AWS_REGION              = var.aws_region
  }
}
