terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }

  # Backend configuration for state management
  # Initialize with: terraform init -backend-config="key=${environment}/terraform.tfstate"
  backend "s3" {
    bucket         = "ytstudybuddy-terraform-state"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "ytstudybuddy-terraform-locks"

    # Enable versioning on the S3 bucket for state history
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}
