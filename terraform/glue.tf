resource "aws_glue_catalog_table" "station_status_raw" {
  name          = var.glue_table_name_status
  database_name = aws_glue_catalog_database.velib.name
  table_type    = "EXTERNAL_TABLE"

  partition_keys {
    name = "year"
    type = "int"
  }

  partition_keys {
    name = "month"
    type = "int"
  }

  partition_keys {
    name = "day"
    type = "int"
  }

  parameters = {
    classification           = "csv"
    EXTERNAL                 = "TRUE"
    "skip.header.line.count" = "1"

    "projection.enabled"        = "true"
    "projection.year.type"      = "integer"
    "projection.year.range"     = "2025,2035"
    "projection.month.type"     = "integer"
    "projection.month.range"    = "1,12"
    "projection.month.digits"   = "2"
    "projection.day.type"       = "integer"
    "projection.day.range"      = "1,31"
    "projection.day.digits"     = "2"
    "storage.location.template" = "s3://${local.velib_bucket_name}/station_status/raw/$${year}/$${month}/$${day}/"
  }

  storage_descriptor {
    location      = "s3://${local.velib_bucket_name}/station_status/raw/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    columns {
      name = "stationcode"
      type = "string"
    }

    columns {
      name = "num_bikes_available"
      type = "int"
    }

    columns {
      name = "num_docks_available"
      type = "int"
    }

    columns {
      name = "is_working"
      type = "int"
    }

    columns {
      name = "num_mechanical_bikes_available"
      type = "int"
    }

    columns {
      name = "num_ebike_bikes_available"
      type = "int"
    }

    columns {
      name = "updated_at"
      type = "timestamp"
    }

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe"

      parameters = {
        "field.delim"          = ","
        "serialization.format" = ","
      }
    }
  }
}

resource "aws_glue_catalog_table" "station_info" {
  name          = var.glue_table_name_info
  database_name = aws_glue_catalog_database.velib.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification           = "csv"
    EXTERNAL                 = "TRUE"
    "skip.header.line.count" = "1"
  }

  storage_descriptor {
    location      = "s3://${local.velib_bucket_name}/station_info/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    columns {
      name = "stationcode"
      type = "string"
    }

    columns {
      name = "name"
      type = "string"
    }

    columns {
      name = "lat"
      type = "double"
    }

    columns {
      name = "lon"
      type = "double"
    }

    columns {
      name = "capacity"
      type = "int"
    }

    columns {
      name = "commune"
      type = "string"
    }

    columns {
      name = "arrondissement"
      type = "int"
    }

    columns {
      name = "commune_arrondissement"
      type = "string"
    }

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe"

      parameters = {
        "field.delim"            = ","
        "serialization.format"   = ","
        "skip.header.line.count" = "1"
      }
    }
  }
}
