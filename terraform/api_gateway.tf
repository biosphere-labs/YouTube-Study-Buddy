# API Gateway HTTP API
resource "aws_apigatewayv2_api" "main" {
  name          = local.api_gateway.name
  protocol_type = "HTTP"
  description   = local.api_gateway.description

  cors_configuration {
    allow_origins = var.domain_name != "" ? [
      "https://${var.domain_name}",
      "http://localhost:3000",
      "http://localhost:8501"
    ] : ["*"]

    allow_methods = [
      "GET",
      "POST",
      "PUT",
      "DELETE",
      "OPTIONS"
    ]

    allow_headers = [
      "Content-Type",
      "Authorization",
      "X-Amz-Date",
      "X-Api-Key",
      "X-Amz-Security-Token"
    ]

    expose_headers = [
      "Content-Length",
      "Content-Type"
    ]

    max_age = 3600
  }

  tags = local.common_tags
}

# Cognito Authorizer
resource "aws_apigatewayv2_authorizer" "cognito" {
  api_id           = aws_apigatewayv2_api.main.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "${local.name_prefix}-cognito-authorizer"

  jwt_configuration {
    audience = [aws_cognito_user_pool_client.main.id]
    issuer   = "https://${aws_cognito_user_pool.main.endpoint}"
  }
}

# API Gateway Stage
resource "aws_apigatewayv2_stage" "main" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = local.api_gateway.stage_name
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      errorMessage   = "$context.error.message"
      integrationErrorMessage = "$context.integrationErrorMessage"
    })
  }

  default_route_settings {
    throttling_burst_limit = 5000
    throttling_rate_limit  = 10000
  }

  tags = local.common_tags
}

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = local.log_groups.api_gateway
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

# Routes and Integrations

# Auth Routes
resource "aws_apigatewayv2_integration" "auth_register" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.auth_register.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "auth_register" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /auth/register"
  target    = "integrations/${aws_apigatewayv2_integration.auth_register.id}"
}

resource "aws_apigatewayv2_integration" "auth_login" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.auth_login.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "auth_login" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /auth/login"
  target    = "integrations/${aws_apigatewayv2_integration.auth_login.id}"
}

resource "aws_apigatewayv2_integration" "auth_refresh" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.auth_refresh.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "auth_refresh" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /auth/refresh"
  target    = "integrations/${aws_apigatewayv2_integration.auth_refresh.id}"
}

resource "aws_apigatewayv2_integration" "auth_verify" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.auth_verify.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "auth_verify" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /auth/verify"
  target    = "integrations/${aws_apigatewayv2_integration.auth_verify.id}"
  authorization_type = "JWT"
  authorizer_id = aws_apigatewayv2_authorizer.cognito.id
}

# Videos Routes
resource "aws_apigatewayv2_integration" "videos_submit" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.videos_submit.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "videos_submit" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /videos"
  target    = "integrations/${aws_apigatewayv2_integration.videos_submit.id}"
  authorization_type = "JWT"
  authorizer_id = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_integration" "videos_list" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.videos_list.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "videos_list" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /videos"
  target    = "integrations/${aws_apigatewayv2_integration.videos_list.id}"
  authorization_type = "JWT"
  authorizer_id = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_integration" "videos_get" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.videos_get.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "videos_get" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /videos/{video_id}"
  target    = "integrations/${aws_apigatewayv2_integration.videos_get.id}"
  authorization_type = "JWT"
  authorizer_id = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_integration" "videos_delete" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.videos_delete.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "videos_delete" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "DELETE /videos/{video_id}"
  target    = "integrations/${aws_apigatewayv2_integration.videos_delete.id}"
  authorization_type = "JWT"
  authorizer_id = aws_apigatewayv2_authorizer.cognito.id
}

# Notes Routes
resource "aws_apigatewayv2_integration" "notes_get" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.notes_get.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "notes_get" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /notes/{note_id}"
  target    = "integrations/${aws_apigatewayv2_integration.notes_get.id}"
  authorization_type = "JWT"
  authorizer_id = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_integration" "notes_list" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.notes_list.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "notes_list" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /notes"
  target    = "integrations/${aws_apigatewayv2_integration.notes_list.id}"
  authorization_type = "JWT"
  authorizer_id = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_integration" "notes_download" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.notes_download.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "notes_download" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /notes/{note_id}/download"
  target    = "integrations/${aws_apigatewayv2_integration.notes_download.id}"
  authorization_type = "JWT"
  authorizer_id = aws_apigatewayv2_authorizer.cognito.id
}

# Credits Routes
resource "aws_apigatewayv2_integration" "credits_get" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.credits_get.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "credits_get" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /credits"
  target    = "integrations/${aws_apigatewayv2_integration.credits_get.id}"
  authorization_type = "JWT"
  authorizer_id = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_integration" "credits_history" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.credits_history.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "credits_history" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /credits/history"
  target    = "integrations/${aws_apigatewayv2_integration.credits_history.id}"
  authorization_type = "JWT"
  authorizer_id = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_integration" "credits_checkout" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.credits_checkout.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "credits_checkout" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /credits/checkout"
  target    = "integrations/${aws_apigatewayv2_integration.credits_checkout.id}"
  authorization_type = "JWT"
  authorizer_id = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_integration" "credits_webhook" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.credits_webhook.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "credits_webhook" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /webhooks/stripe"
  target    = "integrations/${aws_apigatewayv2_integration.credits_webhook.id}"
  # No authorization for webhook - Stripe signature verification in Lambda
}

# User Routes
resource "aws_apigatewayv2_integration" "user_get" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.user_get.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "user_get" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /user"
  target    = "integrations/${aws_apigatewayv2_integration.user_get.id}"
  authorization_type = "JWT"
  authorizer_id = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_integration" "user_update" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.user_update.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "user_update" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "PUT /user"
  target    = "integrations/${aws_apigatewayv2_integration.user_update.id}"
  authorization_type = "JWT"
  authorizer_id = aws_apigatewayv2_authorizer.cognito.id
}
