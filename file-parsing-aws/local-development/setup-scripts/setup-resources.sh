#!/bin/bash

# Setup script for LocalStack resources
echo "Setting up AWS resources in LocalStack..."

# Wait for LocalStack to be ready
echo "Waiting for LocalStack to be ready..."
sleep 10

# Set LocalStack endpoint
export AWS_ENDPOINT_URL=http://localstack:4566

# Create S3 bucket
echo "Creating S3 bucket..."
aws --endpoint-url=$AWS_ENDPOINT_URL s3 mb s3://file-parsing-uploads

# Create DynamoDB tables
echo "Creating DynamoDB tables..."
aws --endpoint-url=$AWS_ENDPOINT_URL dynamodb create-table \
    --table-name records-table \
    --attribute-definitions AttributeName=auth_id,AttributeType=S \
    --key-schema AttributeName=auth_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

aws --endpoint-url=$AWS_ENDPOINT_URL dynamodb create-table \
    --table-name field-mappings-table \
    --attribute-definitions AttributeName=mapping_name,AttributeType=S \
    --key-schema AttributeName=mapping_name,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

# Insert default mapping
echo "Inserting default field mapping..."
aws --endpoint-url=$AWS_ENDPOINT_URL dynamodb put-item \
    --table-name field-mappings-table \
    --item '{
        "mapping_name": {"S": "default"},
        "mappings": {"M": {
            "name": {"L": [{"S": "name"}, {"S": "full_name"}, {"S": "customer_name"}, {"S": "client_name"}]},
            "address1": {"L": [{"S": "address"}, {"S": "address1"}, {"S": "street_address"}, {"S": "street"}]},
            "city": {"L": [{"S": "city"}, {"S": "town"}]},
            "state": {"L": [{"S": "state"}, {"S": "province"}, {"S": "region"}]},
            "zip": {"L": [{"S": "zip"}, {"S": "zipcode"}, {"S": "postal_code"}, {"S": "postalcode"}, {"S": "zip_code"}]},
            "auth_id": {"L": [{"S": "auth_id"}, {"S": "authid"}, {"S": "authorization_id"}, {"S": "auth"}, {"S": "id"}]}
        }}
    }'

# Create SNS topic
echo "Creating SNS topic..."
aws --endpoint-url=$AWS_ENDPOINT_URL sns create-topic --name file-processing-notifications

echo "LocalStack resources setup complete!"