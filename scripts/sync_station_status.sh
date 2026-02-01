#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SOURCE_DIR="$PROJECT_ROOT/data/station_status/raw"

export AWS_PROFILE="allister"

AWS_BIN="${AWS_BIN:-/usr/local/bin/aws}"
if ! command -v "$AWS_BIN" >/dev/null 2>&1; then
  echo "aws not found at $AWS_BIN" >&2
  exit 127
fi

AWS_ACCOUNT_ID="$("$AWS_BIN" sts get-caller-identity --query Account --output text)"

AWS_REGION="eu-west-1"

BUCKET="s3://velib-airflow-${AWS_REGION}-${AWS_ACCOUNT_ID}/station_status/raw"

if [ ! -d "$SOURCE_DIR" ]; then
  echo "Source directory does not exist: $SOURCE_DIR" >&2
  exit 2
fi

"$AWS_BIN" s3 sync "$SOURCE_DIR" "$BUCKET" --delete