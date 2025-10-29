# Cognito User Pool
resource "aws_cognito_user_pool" "main" {
  name = local.cognito_names.user_pool

  # User attributes
  alias_attributes         = ["email", "preferred_username"]
  auto_verified_attributes = ["email"]

  # Password policy
  password_policy {
    minimum_length                   = 8
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = true
    require_uppercase                = true
    temporary_password_validity_days = 7
  }

  # Account recovery
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # User pool schema
  schema {
    name                = "email"
    attribute_data_type = "String"
    mutable             = true
    required            = true

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  schema {
    name                = "name"
    attribute_data_type = "String"
    mutable             = true
    required            = false

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  # Email configuration
  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  # MFA configuration
  mfa_configuration = "OPTIONAL"

  software_token_mfa_configuration {
    enabled = true
  }

  # User pool add-ons
  user_pool_add_ons {
    advanced_security_mode = var.environment == "prod" ? "ENFORCED" : "AUDIT"
  }

  # Username configuration
  username_configuration {
    case_sensitive = false
  }

  # Device configuration
  device_configuration {
    challenge_required_on_new_device      = false
    device_only_remembered_on_user_prompt = true
  }

  # Lambda triggers (optional - add if you have custom authentication flows)
  # lambda_config {
  #   pre_authentication      = aws_lambda_function.pre_auth.arn
  #   post_authentication     = aws_lambda_function.post_auth.arn
  #   pre_token_generation    = aws_lambda_function.pre_token.arn
  # }

  tags = merge(
    local.common_tags,
    {
      Name        = local.cognito_names.user_pool
      Description = "User pool for authentication"
    }
  )
}

# Cognito User Pool Client
resource "aws_cognito_user_pool_client" "main" {
  name         = local.cognito_names.user_pool_client
  user_pool_id = aws_cognito_user_pool.main.id

  # OAuth settings
  generate_secret                      = false
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code", "implicit"]
  allowed_oauth_scopes                 = ["email", "openid", "profile"]

  # Callback URLs
  callback_urls = concat(
    ["http://localhost:3000/callback"],
    var.domain_name != "" ? ["https://${var.domain_name}/callback"] : []
  )

  logout_urls = concat(
    ["http://localhost:3000"],
    var.domain_name != "" ? ["https://${var.domain_name}"] : []
  )

  # Supported identity providers
  supported_identity_providers = concat(
    ["COGNITO"],
    var.google_oauth_client_id != "" ? ["Google"] : [],
    var.github_oauth_client_id != "" ? ["GitHub"] : [],
    var.discord_oauth_client_id != "" ? ["Discord"] : []
  )

  # Token validity
  refresh_token_validity = 30
  access_token_validity  = 60
  id_token_validity      = 60

  token_validity_units {
    refresh_token = "days"
    access_token  = "minutes"
    id_token      = "minutes"
  }

  # Attributes
  read_attributes = [
    "email",
    "email_verified",
    "name",
    "preferred_username",
    "sub"
  ]

  write_attributes = [
    "email",
    "name",
    "preferred_username"
  ]

  # Security settings
  prevent_user_existence_errors = "ENABLED"

  # Enable token revocation
  enable_token_revocation = true

  # Enable propagate additional user attributes
  enable_propagate_additional_user_context_data = false
}

# Cognito User Pool Domain
resource "aws_cognito_user_pool_domain" "main" {
  count = var.cognito_domain_prefix != "" ? 1 : 0

  domain       = var.cognito_domain_prefix
  user_pool_id = aws_cognito_user_pool.main.id
}

# Google Identity Provider
resource "aws_cognito_identity_provider" "google" {
  count = var.google_oauth_client_id != "" ? 1 : 0

  user_pool_id  = aws_cognito_user_pool.main.id
  provider_name = "Google"
  provider_type = "Google"

  provider_details = {
    authorize_scopes = "email profile openid"
    client_id        = var.google_oauth_client_id
    client_secret    = var.google_oauth_client_secret
  }

  attribute_mapping = {
    email    = "email"
    username = "sub"
    name     = "name"
  }
}

# GitHub Identity Provider
resource "aws_cognito_identity_provider" "github" {
  count = var.github_oauth_client_id != "" ? 1 : 0

  user_pool_id  = aws_cognito_user_pool.main.id
  provider_name = "GitHub"
  provider_type = "OIDC"

  provider_details = {
    authorize_scopes              = "user:email read:user"
    client_id                     = var.github_oauth_client_id
    client_secret                 = var.github_oauth_client_secret
    attributes_request_method     = "GET"
    oidc_issuer                   = "https://token.actions.githubusercontent.com"
    authorize_url                 = "https://github.com/login/oauth/authorize"
    token_url                     = "https://github.com/login/oauth/access_token"
    attributes_url                = "https://api.github.com/user"
    jwks_uri                      = "https://token.actions.githubusercontent.com/.well-known/jwks"
  }

  attribute_mapping = {
    email    = "email"
    username = "login"
    name     = "name"
  }
}

# Discord Identity Provider
resource "aws_cognito_identity_provider" "discord" {
  count = var.discord_oauth_client_id != "" ? 1 : 0

  user_pool_id  = aws_cognito_user_pool.main.id
  provider_name = "Discord"
  provider_type = "OIDC"

  provider_details = {
    authorize_scopes              = "identify email"
    client_id                     = var.discord_oauth_client_id
    client_secret                 = var.discord_oauth_client_secret
    attributes_request_method     = "GET"
    oidc_issuer                   = "https://discord.com"
    authorize_url                 = "https://discord.com/api/oauth2/authorize"
    token_url                     = "https://discord.com/api/oauth2/token"
    attributes_url                = "https://discord.com/api/users/@me"
  }

  attribute_mapping = {
    email    = "email"
    username = "username"
    name     = "username"
  }
}

# Cognito Identity Pool
resource "aws_cognito_identity_pool" "main" {
  identity_pool_name               = local.cognito_names.identity_pool
  allow_unauthenticated_identities = false
  allow_classic_flow               = false

  cognito_identity_providers {
    client_id               = aws_cognito_user_pool_client.main.id
    provider_name           = aws_cognito_user_pool.main.endpoint
    server_side_token_check = true
  }

  tags = merge(
    local.common_tags,
    {
      Name        = local.cognito_names.identity_pool
      Description = "Identity pool for federated identities"
    }
  )
}

# IAM role for authenticated users
resource "aws_iam_role" "cognito_authenticated" {
  name = "${local.name_prefix}-cognito-authenticated"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "cognito-identity.amazonaws.com"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "cognito-identity.amazonaws.com:aud" = aws_cognito_identity_pool.main.id
          }
          "ForAnyValue:StringLike" = {
            "cognito-identity.amazonaws.com:amr" = "authenticated"
          }
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM policy for authenticated users
resource "aws_iam_role_policy" "cognito_authenticated" {
  name = "${local.name_prefix}-cognito-authenticated"
  role = aws_iam_role.cognito_authenticated.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cognito-identity:GetId",
          "cognito-identity:GetCredentialsForIdentity"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach role to identity pool
resource "aws_cognito_identity_pool_roles_attachment" "main" {
  identity_pool_id = aws_cognito_identity_pool.main.id

  roles = {
    authenticated = aws_iam_role.cognito_authenticated.arn
  }
}
