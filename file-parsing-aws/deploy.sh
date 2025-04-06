#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="file-parsing-api"
REGION="us-east-1"
S3_BUCKET=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --bucket)
      S3_BUCKET="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --stack-name)
      STACK_NAME="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate S3 bucket
if [ -z "$S3_BUCKET" ]; then
  echo -e "${RED}Error: S3 bucket name is required. Please specify with --bucket BUCKET_NAME${NC}"
  exit 1
fi

echo -e "${YELLOW}Deploying File Parsing API to AWS${NC}"
echo "---------------------------------------------"
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo "S3 Bucket: $S3_BUCKET"
echo "---------------------------------------------"

# Build the application
echo -e "\n${YELLOW}Building the application...${NC}"
sam build || { echo -e "${RED}Build failed${NC}"; exit 1; }

# Package the application
echo -e "\n${YELLOW}Packaging the application...${NC}"
sam package \
  --output-template-file packaged.yaml \
  --s3-bucket $S3_BUCKET \
  --region $REGION || { echo -e "${RED}Packaging failed${NC}"; exit 1; }

# Deploy the application
echo -e "\n${YELLOW}Deploying the application...${NC}"
sam deploy \
  --template-file packaged.yaml \
  --stack-name $STACK_NAME \
  --capabilities CAPABILITY_IAM \
  --region $REGION || { echo -e "${RED}Deployment failed${NC}"; exit 1; }

# Get the outputs
echo -e "\n${YELLOW}Retrieving deployment outputs...${NC}"
aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query "Stacks[0].Outputs" \
  --output table

echo -e "\n${GREEN}Deployment complete!${NC}"
echo -e "To test the deployed API, run:"
echo -e "./local-development/test-api.sh deployed API_ENDPOINT"