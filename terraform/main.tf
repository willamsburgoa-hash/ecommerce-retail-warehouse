# P1 · ecommerce-retail-warehouse — near-zero-cost AWS footprint.
# Services: S3 (tiny) + Glue Data Catalog (free) + Athena workgroup (pay-per-query).
# Run `terraform destroy` at the end of every working session.

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = var.region

  # Tag every resource so AWS Cost Explorer can attribute spend to this project.
  default_tags {
    tags = {
      project    = "ecommerce-retail-warehouse"
      managed_by = "terraform"
    }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "project" {
  type        = string
  description = "Short project slug used in resource names (P1: retail)"
}

variable "suffix" {
  type        = string
  description = "Unique suffix so the S3 bucket name is globally unique"
}

locals {
  bucket_name = "de-portfolio-${var.project}-${var.suffix}"
}

# --- Data lake bucket. raw/, bronze/ and athena-results/ are just key prefixes;
#     they appear on first write from ingest.py / Athena, no resource needed. ---
resource "aws_s3_bucket" "lake" {
  bucket        = local.bucket_name
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "lake" {
  bucket                  = aws_s3_bucket.lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Explicitly unversioned (keeps storage minimal). "Disabled" is only valid at
# creation time; once applied it cannot be set back to Disabled.
resource "aws_s3_bucket_versioning" "lake" {
  bucket = aws_s3_bucket.lake.id
  versioning_configuration {
    status = "Disabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "expire_results" {
  bucket = aws_s3_bucket.lake.id
  rule {
    id     = "expire-athena-results"
    status = "Enabled"
    filter { prefix = "athena-results/" }
    expiration { days = 7 }
  }
}

resource "aws_glue_catalog_database" "db" {
  name = var.project
}

resource "aws_athena_workgroup" "wg" {
  name = "de-portfolio"
  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = false # avoid any CloudWatch cost
    result_configuration {
      output_location = "s3://${aws_s3_bucket.lake.bucket}/athena-results/"
      # No KMS encryption on purpose: extra cost/complexity, no benefit for public sample data.
    }
  }
  force_destroy = true
}

output "s3_bucket" { value = aws_s3_bucket.lake.bucket }
output "glue_database" { value = aws_glue_catalog_database.db.name }
output "athena_workgroup" { value = aws_athena_workgroup.wg.name }
output "athena_output" { value = "s3://${aws_s3_bucket.lake.bucket}/athena-results/" }
