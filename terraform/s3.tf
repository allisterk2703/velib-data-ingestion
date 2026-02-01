resource "aws_s3_bucket" "velib_airflow" {
  bucket = local.velib_bucket_name

  tags = {
    Project   = "velib"
    Component = "airflow"
  }
}

resource "aws_s3_bucket_versioning" "velib_airflow" {
  bucket = aws_s3_bucket.velib_airflow.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "velib_airflow" {
  bucket = aws_s3_bucket.velib_airflow.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
