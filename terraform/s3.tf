# S3 bucket for storing generated notes
resource "aws_s3_bucket" "notes" {
  bucket = local.s3_buckets.notes

  tags = merge(
    local.common_tags,
    {
      Name        = local.s3_buckets.notes
      Description = "Storage for generated study notes"
    }
  )
}

# Enable versioning for notes bucket
resource "aws_s3_bucket_versioning" "notes" {
  bucket = aws_s3_bucket.notes.id

  versioning_configuration {
    status = var.environment == "prod" ? "Enabled" : "Suspended"
  }
}

# Enable encryption for notes bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "notes" {
  bucket = aws_s3_bucket.notes.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access to notes bucket
resource "aws_s3_bucket_public_access_block" "notes" {
  bucket = aws_s3_bucket.notes.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle policy for notes bucket
resource "aws_s3_bucket_lifecycle_configuration" "notes" {
  bucket = aws_s3_bucket.notes.id

  rule {
    id     = "transition-old-notes"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 180
      storage_class = "GLACIER_IR"
    }

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }

  rule {
    id     = "abort-incomplete-uploads"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# CORS configuration for notes bucket
resource "aws_s3_bucket_cors_configuration" "notes" {
  bucket = aws_s3_bucket.notes.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = var.domain_name != "" ? ["https://${var.domain_name}"] : ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3600
  }
}

# Bucket policy for Lambda access
resource "aws_s3_bucket_policy" "notes" {
  bucket = aws_s3_bucket.notes.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowLambdaAccess"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.lambda_execution.arn
        }
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.notes.arn,
          "${aws_s3_bucket.notes.arn}/*"
        ]
      }
    ]
  })
}
