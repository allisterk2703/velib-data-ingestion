# --- IAM ---

resource "aws_iam_role" "lambda_velib_ingestion" {
  name = "lambda-velib-station-status-ingestion"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_velib_logs" {
  role       = aws_iam_role.lambda_velib_ingestion.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_velib_s3" {
  role = aws_iam_role.lambda_velib_ingestion.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:PutObject"]
      Resource = "${aws_s3_bucket.velib_airflow.arn}/station_status/raw/*"
    }]
  })
}

# --- Lambda ---

resource "aws_s3_object" "lambda_zip" {
  bucket = aws_s3_bucket.velib_airflow.id
  key    = "lambda/function.zip"
  source = "${path.module}/../lambda/function.zip"
  etag   = filemd5("${path.module}/../lambda/function.zip")
}

resource "aws_lambda_function" "velib_ingestion" {
  function_name    = "velib-station-status-ingestion"
  s3_bucket        = aws_s3_bucket.velib_airflow.id
  s3_key           = aws_s3_object.lambda_zip.key
  source_code_hash = filebase64sha256("${path.module}/../lambda/function.zip")
  handler          = "handler.handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 256
  architectures    = ["arm64"]
  role             = aws_iam_role.lambda_velib_ingestion.arn

  environment {
    variables = {
      S3_BUCKET = local.velib_bucket_name
    }
  }

  tags = {
    Project   = "velib"
    Component = "ingestion"
  }
}

# --- EventBridge ---

resource "aws_cloudwatch_event_rule" "velib_every_15min" {
  name                = "velib-ingestion-every-15min"
  description         = "Trigger Velib station status ingestion every 15 minutes"
  schedule_expression = "cron(0,15,30,45 * * * ? *)"
}

resource "aws_cloudwatch_event_target" "velib_lambda_target" {
  rule = aws_cloudwatch_event_rule.velib_every_15min.name
  arn  = aws_lambda_function.velib_ingestion.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.velib_ingestion.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.velib_every_15min.arn
}
