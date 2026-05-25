data "aws_caller_identity" "current" {}

locals {
  aws_account_id = data.aws_caller_identity.current.account_id
  region         = var.aws_region

  velib_bucket_name = "velib-airflow-${local.region}-${local.aws_account_id}"
}
