resource "aws_glue_catalog_database" "velib" {
  name = var.glue_database_name
}