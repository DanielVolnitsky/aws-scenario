#!/usr/bin/env bash
set -euo pipefail

BUCKET_NAME="claude-code-metrics-tfstate"
REGION="${AWS_REGION:-us-east-1}"

echo "Creating Terraform state bucket: ${BUCKET_NAME} in ${REGION}"

if aws s3api head-bucket --bucket "${BUCKET_NAME}" 2>/dev/null; then
  echo "Bucket already exists, skipping creation."
else
  if [ "${REGION}" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "${BUCKET_NAME}" --region "${REGION}"
  else
    aws s3api create-bucket --bucket "${BUCKET_NAME}" --region "${REGION}" \
      --create-bucket-configuration LocationConstraint="${REGION}"
  fi

  aws s3api put-bucket-versioning --bucket "${BUCKET_NAME}" \
    --versioning-configuration Status=Enabled

  aws s3api put-public-access-block --bucket "${BUCKET_NAME}" \
    --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

  echo "Bucket created with versioning enabled."
fi

echo ""
echo "Done! Now run:"
echo "  cd ../terraform"
echo "  terraform init"
echo "  terraform apply"
