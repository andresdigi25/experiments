# File Parsing API using AWS Step Functions

This project implements a serverless file parsing solution that can handle different file types and map various column names to a standardized schema. It uses AWS Step Functions to orchestrate the validation, parsing, mapping, and storage of data.

## Architecture

![Architecture Diagram](docs/architecture.png)

This solution uses the following AWS services:
- **S3**: Stores uploaded files
- **Step Functions**: Orchestrates the workflow
- **Lambda**: Executes individual processing steps
- **DynamoDB**: Stores processed data and field mappings
- **API Gateway**: Provides REST API endpoints
- **SNS**: Delivers notifications about processing results
- **EventBridge**: Triggers workflow when files are uploaded to S3

## Project Structure

```
file-parsing-api/
├── functions/                 # Lambda function code
│   ├── validate_file/         # Validates file format
│   ├── determine_file_type/   # Determines file type
│   ├── parse_file/            # Parses file contents
│   ├── map_fields/            # Maps fields to standard schema
│   ├── store_data/            # Stores data in DynamoDB
│   ├── report_success/        # Reports successful processing
│   ├── report_failure/        # Reports processing failures
│   ├── manage_field_mappings/ # API for field mappings
│   ├── file_upload/           # File upload API
│   └── initiate_file_processing/ # Triggers Step Functions
├── statemachine/              # Step Functions definition
│   └── file_processing.asl.json
├── template.yaml              # SAM template
├── local-development/         # Local development utilities
│   ├── docker-compose.yml     # LocalStack configuration
│   ├── setup-scripts/         # Setup scripts for LocalStack
│   ├── start-local.sh         # Start local development environment
│   └── test-api.sh            # Test script for API
├── sample_files/              # Sample files for testing
│   ├── sample_data.csv
│   ├── sample_data.json
│   └── sample_data.txt
├── deploy.sh                  # Deployment script
└── README.md                  # This file
```

## Running Locally

### Using AWS SAM

1. Install prerequisites:
   - [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
   - [Docker](https://www.docker.com/get-started)

2. Start the local development environment:
   ```bash
   cd local-development
   chmod +x start-local.sh
   ./start-local.sh
   ```

3. Test the API:
   ```bash
   chmod +x test-api.sh
   ./test-api.sh
   ```

### Using LocalStack

1. Start LocalStack environment:
   ```bash
   cd local-development
   docker-compose up -d
   ```

2. Use AWS CLI with LocalStack endpoint:
   ```bash
   aws --endpoint-url=http://localhost:4566 s3 ls
   ```

3. Test the API (after deploying functions to LocalStack):
   ```bash
   ./test-api.sh
   ```

## Deploying to AWS

1. Create an S3 bucket for deployment artifacts:
   ```bash
   aws s3 mb s3://your-deployment-bucket
   ```

2. Deploy using the deployment script:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh --bucket your-deployment-bucket --region us-east-1 --stack-name file-parsing-api
   ```

3. Test the deployed API:
   ```bash
   ./local-development/test-api.sh deployed https://your-api-endpoint.execute-api.us-east-1.amazonaws.com/Prod
   ```

## Sample Files

The `sample_files` directory contains example files to test the API:
- `sample_data.csv`: Standard CSV format
- `sample_data.json`: JSON data with different field names
- `sample_data.txt`: Tab-delimited text file

## Field Mappings

Field mappings define how source column names are mapped to the standard schema fields. The default mapping includes:

```json
{
  "name": ["name", "full_name", "customer_name", "client_name"],
  "address1": ["address", "address1", "street_address", "street"],
  "city": ["city", "town"],
  "state": ["state", "province", "region"],
  "zip": ["zip", "zipcode", "postal_code", "postalcode", "zip_code"],
  "auth_id": ["auth_id", "authid", "authorization_id", "auth", "id"]
}
```

You can add custom mappings through the API:
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "name": "vendor2",
    "mappings": {
      "name": ["client_name", "customer"],
      "address1": ["billing_address", "primary_address"],
      "city": ["billing_city"],
      "state": ["billing_state"],
      "zip": ["billing_zip"],
      "auth_id": ["client_code"]
    }
  }' \
  https://your-api-endpoint.execute-api.us-east-1.amazonaws.com/Prod/mappings
```

## API Reference

- **POST /upload**
  - Upload a file for processing
  - Parameters:
    - `file`: The file to upload
    - `source`: Field mapping source name (default: "default")

- **POST /process**
  - Initiate processing for a file in S3
  - Body:
    ```json
    {
      "bucket": "your-bucket",
      "key": "path/to/file.csv",
      "mappingSource": "default"
    }
    ```

- **GET /mappings**
  - Get all field mappings

- **POST /mappings**
  - Create a new field mapping
  - Body:
    ```json
    {
      "name": "mapping-name",
      "mappings": {
        "name": ["source_field1", "source_field2"],
        "address1": ["source_field3", "source_field4"],
        ...
      }
    }
    ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.