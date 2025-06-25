# main.tf

# ----------------------------------------------------
# AWS Provider Info
# ----------------------------------------------------

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  required_version = ">= 1.3.0"
}

provider "aws" {
  region = var.region
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

# ----------------------------------------------------
# AWS Account Info (used for bucket policy)
# ----------------------------------------------------
data "aws_caller_identity" "current" {}


# ----------------------------------------------------
# S3 Bucket for Static Website Hosting
# ----------------------------------------------------

resource "aws_s3_bucket" "website_bucket" {
  bucket = "${var.project_name}-${var.owner_name}"
  force_destroy = true

  tags = {
    Name    = "${var.project_name}-${var.owner_name}"
    Project = var.project_name
  }
}

# ----------------------------------------------------
# Block Public Access
# ----------------------------------------------------

resource "aws_s3_bucket_public_access_block" "website_public_access" {
  bucket = aws_s3_bucket.website_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ----------------------------------------------------
# Server Side Encryption
# ----------------------------------------------------

resource "aws_s3_bucket_server_side_encryption_configuration" "website_encryption" {
  bucket = aws_s3_bucket.website_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ----------------------------------------------------
# Enable Versioning
# ----------------------------------------------------

resource "aws_s3_bucket_versioning" "website_versioning" {
  bucket = aws_s3_bucket.website_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}


# ----------------------------------------------------
# ACM Certificate
# ----------------------------------------------------

resource "aws_acm_certificate" "website_cert" {
  provider          = aws.us_east_1
  domain_name       = "${var.subdomain}.${var.domain_name}"
  validation_method = "DNS"

  tags = {
    Name    = "${var.project_name}-cert"
    Project = var.project_name
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ----------------------------------------------------
# Find Hosted Zone
# ----------------------------------------------------
data "aws_route53_zone" "selected" {
  name         = var.domain_name
  private_zone = false
}

# ----------------------------------------------------
# Create Validation Record
# ----------------------------------------------------
resource "aws_route53_record" "website_cert_validation" {
  zone_id = data.aws_route53_zone.selected.zone_id
  name    = element(toset(aws_acm_certificate.website_cert.domain_validation_options).*.resource_record_name, 0)
  type    = element(toset(aws_acm_certificate.website_cert.domain_validation_options).*.resource_record_type, 0)
  records = [element(toset(aws_acm_certificate.website_cert.domain_validation_options).*.resource_record_value, 0)]

  ttl     = 60
}

# ----------------------------------------------------
# Wait for Validation to Complete
# ----------------------------------------------------

resource "aws_acm_certificate_validation" "website_cert_validation_wait" {
  provider                = aws.us_east_1
  certificate_arn         = aws_acm_certificate.website_cert.arn
  validation_record_fqdns = [aws_route53_record.website_cert_validation.fqdn]
}

# ----------------------------------------------------
# Origin Access Control
# ----------------------------------------------------

resource "aws_cloudfront_origin_access_control" "website_oac" {
  name                              = "${var.project_name}-oac"
  description                       = "OAC for CloudFront to access S3"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# ----------------------------------------------------
# CloudFront Distribution
# ----------------------------------------------------

resource "aws_cloudfront_distribution" "website_distribution" {
  origin {
    domain_name              = aws_s3_bucket.website_bucket.bucket_regional_domain_name
    origin_id                = aws_s3_bucket.website_bucket.id
    origin_access_control_id = aws_cloudfront_origin_access_control.website_oac.id
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = aws_s3_bucket.website_bucket.id
    viewer_protocol_policy = "redirect-to-https"

    cache_policy_id = data.aws_cloudfront_cache_policy.optimized.id
  }

  viewer_certificate {
    acm_certificate_arn            = aws_acm_certificate_validation.website_cert_validation_wait.certificate_arn
    ssl_support_method             = "sni-only"
    minimum_protocol_version       = "TLSv1.2_2021"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  aliases = ["${var.subdomain}.${var.domain_name}"]

  tags = {
    Name    = "${var.project_name}-cloudfront"
    Project = var.project_name
  }

  depends_on = [aws_acm_certificate_validation.website_cert_validation_wait]
}

# ----------------------------------------------------
# Cache policy fix
# ----------------------------------------------------
data "aws_cloudfront_cache_policy" "optimized" {
  name = "Managed-CachingOptimized"
}


# ----------------------------------------------------
# Route 53 Alias Record
# ----------------------------------------------------

resource "aws_route53_record" "website_alias_record" {
  zone_id = data.aws_route53_zone.selected.zone_id
  name    = "${var.subdomain}.${var.domain_name}"
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.website_distribution.domain_name
    zone_id                = aws_cloudfront_distribution.website_distribution.hosted_zone_id
    evaluate_target_health = false
  }

  depends_on = [
    aws_acm_certificate_validation.website_cert_validation_wait
  ]
}

# ----------------------------------------------------
# S3 bucket policy for Cloudfront OAC
# ----------------------------------------------------

resource "aws_s3_bucket_policy" "website_policy" {
  bucket = aws_s3_bucket.website_bucket.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontOAC"
        Effect    = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.website_bucket.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = "arn:aws:cloudfront::${data.aws_caller_identity.current.account_id}:distribution/${aws_cloudfront_distribution.website_distribution.id}"
          }
        }
      }
    ]
  })
}
