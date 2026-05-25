#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ENV_FILE="$PROJECT_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
  set -a
  source "$ENV_FILE"
  set +a
fi

: "${AWS_PROFILE:?AWS_PROFILE must be set (e.g. in .env)}"
: "${AWS_REGION:?AWS_REGION must be set (e.g. in .env)}"

export AWS_PROFILE AWS_REGION

AWS_BIN="${AWS_BIN:-/usr/local/bin/aws}"

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <source_path> <destination_folder_name>"
    exit 1
fi

INPUT_PATH="$1"
DEST_FOLDER="$2"

if ! command -v "$AWS_BIN" >/dev/null 2>&1; then
  echo "Error: aws CLI not found" >&2
  exit 127
fi

AWS_ACCOUNT_ID="$("$AWS_BIN" sts get-caller-identity --query Account --output text)"
BASE_BUCKET="s3://velib-airflow-${AWS_REGION}-${AWS_ACCOUNT_ID}"

if [[ "$INPUT_PATH" != /* ]]; then
    FULL_PATH="$PROJECT_ROOT/$INPUT_PATH"
else
    FULL_PATH="$INPUT_PATH"
fi

if [ -f "$FULL_PATH" ]; then
    FILENAME=$(basename "$FULL_PATH")
    "$AWS_BIN" s3 cp "$FULL_PATH" "$BASE_BUCKET/$DEST_FOLDER/$FILENAME"
elif [ -d "$FULL_PATH" ]; then
    "$AWS_BIN" s3 sync "$FULL_PATH" "$BASE_BUCKET/$DEST_FOLDER/" --delete
else
    echo "Error: Path not found: $FULL_PATH" >&2
    exit 2
fi