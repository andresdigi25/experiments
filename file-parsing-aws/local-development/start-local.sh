#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up local AWS environment for file parsing API${NC}"
echo "---------------------------------------------"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo -e "${RED}Error: Docker is not running. Please start Docker and try again.${NC}"
  exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
  echo -e "${RED}Error: AWS SAM CLI is not installed. Please install it:${NC}"
  echo "https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html"
  exit 1
fi

# Create necessary directories
echo -e "\n${YELLOW}Creating necessary directories...${NC}"
mkdir -p .aws-sam/build
mkdir -p sam-local-data
mkdir -p sample_files

# Copy sample files to the sample_files directory
echo -e "\n${YELLOW}Creating sample test files...${NC}"

# Sample CSV file
cat > sample_files/sample_data.csv << 'EOF'
full_name,street_address,city,state,zipcode,auth_id
John Doe,123 Main St,New York,NY,10001,AUTH001
Jane Smith,456 Park Ave,Los Angeles,CA,90001,AUTH002
Robert Johnson,789 Broadway,Chicago,IL,60601,AUTH003
Emily Williams,321 Oak St,Houston,TX,77001,AUTH004
Michael Brown,654 Pine Rd,Phoenix,AZ,85001,AUTH005
EOF

# Sample JSON file
cat > sample_files/sample_data.json << 'EOF'
[
  {
    "name": "Thomas Anderson",
    "address": "555 Matrix St",
    "city": "San Francisco",
    "state": "CA",
    "postal_code": "94105",
    "authorization_id": "JSON001"
  },
  {
    "name": "Sarah Connor",
    "address": "888 Skynet Ave",
    "city": "San Diego",
    "state": "CA",
    "postal_code": "92101",
    "authorization_id": "JSON002"
  }
]
EOF

# Sample text file
cat > sample_files/sample_data.txt << 'EOF'
client_name	street	town	region	zip_code	id
Bruce Wayne	1 Wayne Manor	Gotham	NJ	07101	TXT001
Clark Kent	344 Clinton St	Metropolis	NY	10001	TXT002
Diana Prince	1720 H St NW	Washington	DC	20006	TXT003
EOF

# Create environment variables file for SAM
echo -e "\n${YELLOW}Creating SAM environment file...${NC}"
cat > env.json << 'EOF'
{
  "Parameters": {
    "UPLOAD_BUCKET": "local-upload-bucket",
    "DYNAMODB_TABLE": "local-records-table",
    "FIELD_MAPPINGS_TABLE": "local-field-mappings-table",
    "STATE_MACHINE_ARN": "arn:aws:states:local:000000000000:stateMachine:file-processing-state-machine",
    "SNS_TOPIC_ARN": "arn:aws:sns:local:000000000000:file-processing-notifications"
  }
}
EOF

# Start SAM local API
echo -e "\n${YELLOW}Starting SAM local API...${NC}"
sam local start-api --env-vars env.json --docker-network sam-local

echo -e "\n${GREEN}Local API is running. Press Ctrl+C to stop.${NC}"