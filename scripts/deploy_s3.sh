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

# The public site is fronted by CloudFront, so S3 uploads alone leave visitors
# on cached HTML until the edge caches are invalidated.
if [ -n "${CLOUDFRONT_DISTRIBUTION_ID:-}" ]; then
  ID=$(aws cloudfront create-invalidation \
    --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
    --paths '/*' \
    --query 'Invalidation.Id' --output text)
  echo "Created CloudFront invalidation $ID on $CLOUDFRONT_DISTRIBUTION_ID"
  aws cloudfront wait invalidation-completed \
    --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" --id "$ID"
  echo "Invalidation $ID completed"
else
  echo "WARNING: CLOUDFRONT_DISTRIBUTION_ID not set; skipping cache invalidation."
  echo "         Visitors may keep seeing cached content."
fi
