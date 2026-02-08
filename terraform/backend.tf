terraform {
  backend "s3" {
    bucket         = "velib-data-ingestion-terraform-state-eu-west-1-217831684037"
    key            = "velib/terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
