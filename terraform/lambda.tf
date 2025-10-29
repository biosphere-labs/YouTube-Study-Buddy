# Lambda Layer for CLI dependencies
resource "aws_lambda_layer_version" "cli" {
  filename            = "${path.module}/lambda_layers/cli_layer.zip"
  layer_name          = local.lambda_layers.cli
  compatible_runtimes = [var.lambda_runtime]
  description         = "YouTube Study Buddy CLI and dependencies"

  source_code_hash = fileexists("${path.module}/lambda_layers/cli_layer.zip") ? filebase64sha256("${path.module}/lambda_layers/cli_layer.zip") : null

  lifecycle {
    ignore_changes = [source_code_hash]
  }
}

# CloudWatch Log Groups for Lambda functions
resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each = local.lambda_functions

  name              = "/aws/lambda/${each.value}"
  retention_in_days = var.log_retention_days

  tags = merge(
    local.common_tags,
    {
      Name = "${each.value}-logs"
    }
  )
}

# Auth: Register
resource "aws_lambda_function" "auth_register" {
  filename         = "${path.module}/lambda_functions/auth_register.zip"
  function_name    = local.lambda_functions.auth_register
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = 256

  source_code_hash = fileexists("${path.module}/lambda_functions/auth_register.zip") ? filebase64sha256("${path.module}/lambda_functions/auth_register.zip") : null

  environment {
    variables = local.lambda_env_vars
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]

  lifecycle {
    ignore_changes = [source_code_hash]
  }

  tags = local.common_tags
}

# Auth: Login
resource "aws_lambda_function" "auth_login" {
  filename         = "${path.module}/lambda_functions/auth_login.zip"
  function_name    = local.lambda_functions.auth_login
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = 256

  source_code_hash = fileexists("${path.module}/lambda_functions/auth_login.zip") ? filebase64sha256("${path.module}/lambda_functions/auth_login.zip") : null

  environment {
    variables = local.lambda_env_vars
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]

  lifecycle {
    ignore_changes = [source_code_hash]
  }

  tags = local.common_tags
}

# Auth: Refresh Token
resource "aws_lambda_function" "auth_refresh" {
  filename         = "${path.module}/lambda_functions/auth_refresh.zip"
  function_name    = local.lambda_functions.auth_refresh
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = 256

  source_code_hash = fileexists("${path.module}/lambda_functions/auth_refresh.zip") ? filebase64sha256("${path.module}/lambda_functions/auth_refresh.zip") : null

  environment {
    variables = local.lambda_env_vars
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]

  lifecycle {
    ignore_changes = [source_code_hash]
  }

  tags = local.common_tags
}

# Auth: Verify Token
resource "aws_lambda_function" "auth_verify" {
  filename         = "${path.module}/lambda_functions/auth_verify.zip"
  function_name    = local.lambda_functions.auth_verify
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = 256

  source_code_hash = fileexists("${path.module}/lambda_functions/auth_verify.zip") ? filebase64sha256("${path.module}/lambda_functions/auth_verify.zip") : null

  environment {
    variables = local.lambda_env_vars
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]

  lifecycle {
    ignore_changes = [source_code_hash]
  }

  tags = local.common_tags
}

# Videos: Submit
resource "aws_lambda_function" "videos_submit" {
  filename         = "${path.module}/lambda_functions/videos_submit.zip"
  function_name    = local.lambda_functions.videos_submit
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = 256

  source_code_hash = fileexists("${path.module}/lambda_functions/videos_submit.zip") ? filebase64sha256("${path.module}/lambda_functions/videos_submit.zip") : null

  environment {
    variables = local.lambda_env_vars
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]

  lifecycle {
    ignore_changes = [source_code_hash]
  }

  tags = local.common_tags
}

# Videos: List
resource "aws_lambda_function" "videos_list" {
  filename         = "${path.module}/lambda_functions/videos_list.zip"
  function_name    = local.lambda_functions.videos_list
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = 256

  source_code_hash = fileexists("${path.module}/lambda_functions/videos_list.zip") ? filebase64sha256("${path.module}/lambda_functions/videos_list.zip") : null

  environment {
    variables = local.lambda_env_vars
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]

  lifecycle {
    ignore_changes = [source_code_hash]
  }

  tags = local.common_tags
}

# Videos: Get
resource "aws_lambda_function" "videos_get" {
  filename         = "${path.module}/lambda_functions/videos_get.zip"
  function_name    = local.lambda_functions.videos_get
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = 256

  source_code_hash = fileexists("${path.module}/lambda_functions/videos_get.zip") ? filebase64sha256("${path.module}/lambda_functions/videos_get.zip") : null

  environment {
    variables = local.lambda_env_vars
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]

  lifecycle {
    ignore_changes = [source_code_hash]
  }

  tags = local.common_tags
}

# Videos: Delete
resource "aws_lambda_function" "videos_delete" {
  filename         = "${path.module}/lambda_functions/videos_delete.zip"
  function_name    = local.lambda_functions.videos_delete
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = 256

  source_code_hash = fileexists("${path.module}/lambda_functions/videos_delete.zip") ? filebase64sha256("${path.module}/lambda_functions/videos_delete.zip") : null

  environment {
    variables = local.lambda_env_vars
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]

  lifecycle {
    ignore_changes = [source_code_hash]
  }

  tags = local.common_tags
}

# Videos: Process (SQS consumer)
resource "aws_lambda_function" "videos_process" {
  filename         = "${path.module}/lambda_functions/videos_process.zip"
  function_name    = local.lambda_functions.videos_process
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size
  layers          = [aws_lambda_layer_version.cli.arn]

  source_code_hash = fileexists("${path.module}/lambda_functions/videos_process.zip") ? filebase64sha256("${path.module}/lambda_functions/videos_process.zip") : null

  environment {
    variables = local.lambda_env_vars
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]

  lifecycle {
    ignore_changes = [source_code_hash]
  }

  tags = local.common_tags
}

# Event source mapping: SQS -> Lambda
resource "aws_lambda_event_source_mapping" "video_processing" {
  event_source_arn = aws_sqs_queue.video_processing.arn
  function_name    = aws_lambda_function.videos_process.arn
  batch_size       = 1
  enabled          = true

  scaling_config {
    maximum_concurrency = 10
  }

  function_response_types = ["ReportBatchItemFailures"]
}

# Notes: Get
resource "aws_lambda_function" "notes_get" {
  filename         = "${path.module}/lambda_functions/notes_get.zip"
  function_name    = local.lambda_functions.notes_get
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = 256

  source_code_hash = fileexists("${path.module}/lambda_functions/notes_get.zip") ? filebase64sha256("${path.module}/lambda_functions/notes_get.zip") : null

  environment {
    variables = local.lambda_env_vars
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]

  lifecycle {
    ignore_changes = [source_code_hash]
  }

  tags = local.common_tags
}

# Notes: List
resource "aws_lambda_function" "notes_list" {
  filename         = "${path.module}/lambda_functions/notes_list.zip"
  function_name    = local.lambda_functions.notes_list
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = 256

  source_code_hash = fileexists("${path.module}/lambda_functions/notes_list.zip") ? filebase64sha256("${path.module}/lambda_functions/notes_list.zip") : null

  environment {
    variables = local.lambda_env_vars
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]

  lifecycle {
    ignore_changes = [source_code_hash]
  }

  tags = local.common_tags
}

# Notes: Download
resource "aws_lambda_function" "notes_download" {
  filename         = "${path.module}/lambda_functions/notes_download.zip"
  function_name    = local.lambda_functions.notes_download
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = 256

  source_code_hash = fileexists("${path.module}/lambda_functions/notes_download.zip") ? filebase64sha256("${path.module}/lambda_functions/notes_download.zip") : null

  environment {
    variables = local.lambda_env_vars
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]

  lifecycle {
    ignore_changes = [source_code_hash]
  }

  tags = local.common_tags
}

# Credits: Get Balance
resource "aws_lambda_function" "credits_get" {
  filename         = "${path.module}/lambda_functions/credits_get.zip"
  function_name    = local.lambda_functions.credits_get
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = 256

  source_code_hash = fileexists("${path.module}/lambda_functions/credits_get.zip") ? filebase64sha256("${path.module}/lambda_functions/credits_get.zip") : null

  environment {
    variables = local.lambda_env_vars
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]

  lifecycle {
    ignore_changes = [source_code_hash]
  }

  tags = local.common_tags
}

# Credits: Get History
resource "aws_lambda_function" "credits_history" {
  filename         = "${path.module}/lambda_functions/credits_history.zip"
  function_name    = local.lambda_functions.credits_history
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = 256

  source_code_hash = fileexists("${path.module}/lambda_functions/credits_history.zip") ? filebase64sha256("${path.module}/lambda_functions/credits_history.zip") : null

  environment {
    variables = local.lambda_env_vars
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]

  lifecycle {
    ignore_changes = [source_code_hash]
  }

  tags = local.common_tags
}

# Credits: Checkout
resource "aws_lambda_function" "credits_checkout" {
  filename         = "${path.module}/lambda_functions/credits_checkout.zip"
  function_name    = local.lambda_functions.credits_checkout
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = 256

  source_code_hash = fileexists("${path.module}/lambda_functions/credits_checkout.zip") ? filebase64sha256("${path.module}/lambda_functions/credits_checkout.zip") : null

  environment {
    variables = local.lambda_env_vars
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]

  lifecycle {
    ignore_changes = [source_code_hash]
  }

  tags = local.common_tags
}

# Credits: Webhook
resource "aws_lambda_function" "credits_webhook" {
  filename         = "${path.module}/lambda_functions/credits_webhook.zip"
  function_name    = local.lambda_functions.credits_webhook
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = 256

  source_code_hash = fileexists("${path.module}/lambda_functions/credits_webhook.zip") ? filebase64sha256("${path.module}/lambda_functions/credits_webhook.zip") : null

  environment {
    variables = local.lambda_env_vars
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]

  lifecycle {
    ignore_changes = [source_code_hash]
  }

  tags = local.common_tags
}

# User: Get Profile
resource "aws_lambda_function" "user_get" {
  filename         = "${path.module}/lambda_functions/user_get.zip"
  function_name    = local.lambda_functions.user_get
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = 256

  source_code_hash = fileexists("${path.module}/lambda_functions/user_get.zip") ? filebase64sha256("${path.module}/lambda_functions/user_get.zip") : null

  environment {
    variables = local.lambda_env_vars
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]

  lifecycle {
    ignore_changes = [source_code_hash]
  }

  tags = local.common_tags
}

# User: Update Profile
resource "aws_lambda_function" "user_update" {
  filename         = "${path.module}/lambda_functions/user_update.zip"
  function_name    = local.lambda_functions.user_update
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = 256

  source_code_hash = fileexists("${path.module}/lambda_functions/user_update.zip") ? filebase64sha256("${path.module}/lambda_functions/user_update.zip") : null

  environment {
    variables = local.lambda_env_vars
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]

  lifecycle {
    ignore_changes = [source_code_hash]
  }

  tags = local.common_tags
}

# Lambda permissions for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  for_each = {
    auth_register    = aws_lambda_function.auth_register
    auth_login       = aws_lambda_function.auth_login
    auth_refresh     = aws_lambda_function.auth_refresh
    auth_verify      = aws_lambda_function.auth_verify
    videos_submit    = aws_lambda_function.videos_submit
    videos_list      = aws_lambda_function.videos_list
    videos_get       = aws_lambda_function.videos_get
    videos_delete    = aws_lambda_function.videos_delete
    notes_get        = aws_lambda_function.notes_get
    notes_list       = aws_lambda_function.notes_list
    notes_download   = aws_lambda_function.notes_download
    credits_get      = aws_lambda_function.credits_get
    credits_history  = aws_lambda_function.credits_history
    credits_checkout = aws_lambda_function.credits_checkout
    credits_webhook  = aws_lambda_function.credits_webhook
    user_get         = aws_lambda_function.user_get
    user_update      = aws_lambda_function.user_update
  }

  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = each.value.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}
