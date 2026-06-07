resource "aws_s3_bucket" "velib_bucket" {
  bucket = local.velib_bucket_name

  tags = {
    Project   = "velib"
    Component = "storage"
  }
}

resource "aws_s3_bucket_versioning" "velib_bucket" {
  bucket = aws_s3_bucket.velib_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "velib_bucket" {
  bucket = aws_s3_bucket.velib_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "velib_bucket" {
  bucket = aws_s3_bucket.velib_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "velib_bucket" {
  bucket = aws_s3_bucket.velib_bucket.id

  rule {
    id     = "raw-data-to-ia"
    status = "Enabled"

    filter {
      prefix = "station_status/raw/"
    }

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }
  }

  rule {
    id     = "expire-noncurrent-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}
