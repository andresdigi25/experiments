# Commands Guide for File Parsing API

This document provides a comprehensive list of commands to set up, run, test, and deploy the File Parsing API.

## Initial Setup

### 1. Clone the repository and set up project structure

```bash
# Create project directory
mkdir -p file-parsing-api
cd file-parsing-api

# Create directory structure
mkdir -p functions/validate_file
mkdir -p functions/determine_file_type
mkdir -p functions/parse_file
mkdir -p functions/map_fields
mkdir -p functions/store_data
mkdir -p functions/report_success
mkdir -p functions/report_failure
mkdir -p functions/manage_field_mappings
mkdir -p functions/file_upload
mkdir -p functions/initiate_file_processing
mkdir -p statemachine
mkdir -p local-development/setup-scripts
mkdir -p sample_files
```

### 2. Make scripts executable

```bash
chmod +x deploy.sh
chmod +x local-development/start-local.sh
chmod +x local-development/test-api.sh
chmod +x local-development/setup-scripts/setup-resources.sh
```

## Running Locally

### 1. Using AWS SAM

```bash
# Start local development environment with SAM
cd local-development
./start-local.sh

# In a new terminal, test the API
./test-api.sh
```

### 2. Using LocalStack

```bash
# Start LocalStack
cd local-development
docker-compose up -d

# Wait for setup to complete, then test with AWS CLI
aws --endpoint-url=http://localhost:4566 s3 ls
aws --endpoint-url=http://localhost:4566 dynamodb scan --table-name field-mappings-table

# Build and package for LocalStack (simplified approach)
sam build --use-container
sam local invoke ValidateFileFunction --event events/test-event.json

# Test the API against LocalStack (requires extra setup)
./test-api.sh
```

## Testing

### 1. Test individual functions locally

```bash
# Test a function with a sample event
sam local invoke ValidateFileFunction --event events/test-validate-file-event.json

# Test multiple functions in sequence
sam local invoke-api --event events/test-api-event.json
```

### 2. Test Step Functions workflow locally

```bash
# Start a local Step Functions server (not officially supported by SAM, but possible with extensions)
sam local start-lambda
aws --endpoint-url=http://localhost:3001 stepfunctions start-execution \
  --state-machine arn:aws:states:us-east-1:123456789012:stateMachine:file-processing \
  --input '{"bucket":"test-bucket","key":"sample_files/sample_data.csv","mappingSource":"default"}'
```

### 3. Run integration tests

```bash
# Test file upload and processing
curl -X POST \
  -F "file=@sample_files/sample_data.csv" \
  -F "source=default" \
  http://localhost:3000/upload

# Test field mapping API
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-mapping",
    "mappings": {
      "name": ["test_name"],
      "address1": ["test_address"],
      "city": ["test_city"],
      "state": ["test_state"],
      "zip": ["test_zip"],
      "auth_id": ["test_id"]
    }
  }' \
  http://localhost:3000/mappings

# Get all mappings
curl http://localhost:3000/mappings
```

## Deploying to AWS

### 1. Build and package with SAM

```bash
# Build the application
sam build

# Package for deployment (replace with your S3 bucket)
sam package \
  --output-template-file packaged.yaml \
  --s3-bucket your-deployment-bucket
```

### 2. Deploy with SAM

```bash
# Deploy the application
sam deploy \
  --template-file packaged.yaml \
  --stack-name file-parsing-api \
  --capabilities CAPABILITY_IAM

# Or use guided deployment
sam deploy --guided
```

### 3. Using the deployment script

```bash
# Deploy using the script (easier option)
./deploy.sh --bucket your-deployment-bucket --region us-east-1 --stack-name file-parsing-api
```

### 4. Test the deployed API

```bash
# Get the API endpoint
aws cloudformation describe-stacks \
  --stack-name file-parsing-api \
  --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
  --output text

# Test the deployed API
./local-development/test-api.sh deployed https://your-api-endpoint.execute-api.us-east-1.amazonaws.com/Prod
```

## Clean Up

### 1. Delete local resources

```bash
# Stop LocalStack
cd local-development
docker-compose down -v

# Delete local data
rm -rf .aws-sam
rm -rf sam-local-data
```

### 2. Delete AWS resources

```bash
# Delete the CloudFormation stack
aws cloudformation delete-stack --stack-name file-parsing-api

# Delete deployment artifacts from S3
aws s3 rm s3://your-deployment-bucket --recursive --exclude "*" --include "file-parsing-api/*"
```