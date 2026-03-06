#!/bin/bash
set -euo pipefail

BUCKET="${S3_BUCKET_NAME:?S3_BUCKET_NAME must be set}"
BUILD_DIR="$(dirname "$0")/../build"

if [ ! -d "$BUILD_DIR" ]; then
  echo "Error: build directory not found. Run generate_site.py first."
  exit 1
fi

aws s3 sync "$BUILD_DIR" "s3://$BUCKET" --delete
echo "Deployed to s3://$BUCKET"
