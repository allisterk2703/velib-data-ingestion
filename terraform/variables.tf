variable "aws_region" {
  description = "AWS region where resources are deployed"
  type        = string
  default     = "eu-west-1"
}

variable "glue_database_name" {
  description = "Glue database name for raw Velib data"
  type        = string
  default     = "velib_data_ingestion"
}

variable "glue_table_name_status" {
  description = "Glue table name for station status raw CSV"
  type        = string
  default     = "station_status_raw"
}

variable "glue_table_name_info" {
  description = "Glue table name for station status raw CSV"
  type        = string
  default     = "station_info"
}
