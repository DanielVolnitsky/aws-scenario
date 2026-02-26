terraform {
  # Minimum Terraform version required to run this config
  required_version = ">= 1.5"

  # Download the AWS plugin (v5.x) from HashiCorp's registry —
  # this is what lets Terraform create/manage AWS resources
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Where Terraform saves its "memory" of what it created (the state file).
  # Without this, Terraform wouldn't know what resources already exist.
  # The S3 bucket is created by bootstrap/bootstrap.sh — replace ACCOUNT_ID
  # with your actual AWS account ID.
  backend "s3" {
    bucket = "claude-code-metrics-tfstate-ACCOUNT_ID"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}

# How Terraform talks to AWS: which region to deploy into,
# and default labels slapped on every resource so you can tell
# in the AWS console "this was made by Terraform for this project"
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = var.project_name
      ManagedBy = "terraform"
    }
  }
}

# Asks AWS "which account am I logged in as?" — makes the account ID
# available to other .tf files (e.g. for ARNs) without hardcoding it
data "aws_caller_identity" "current" {}
