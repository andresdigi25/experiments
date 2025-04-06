#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Testing File Parsing API${NC}"
echo "---------------------------------------------"

# Determine if we're using SAM local or deployed API
if [ "$1" == "deployed" ]; then
  API_URL=$2
  echo -e "${YELLOW}Using deployed API at: $API_URL${NC}"
else
  API_URL="http://localhost:3000"
  echo -e "${YELLOW}Using local API at: $API_URL${NC}"
fi

# 1. Add vendor2 mapping configuration
echo -e "\n${YELLOW}1. Adding vendor2 mapping configuration...${NC}"
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
  ${API_URL}/mappings
echo ""

# 2. Test with standard CSV file
echo -e "\n${YELLOW}2. Testing with standard CSV file...${NC}"
curl -X POST \
  -F "file=@../sample_files/sample_data.csv" \
  -F "source=default" \
  ${API_URL}/upload
echo ""

# 3. Get all mapping configurations
echo -e "\n${YELLOW}3. Getting all mapping configurations...${NC}"
curl ${API_URL}/mappings
echo ""

# 4. Process a file directly
echo -e "\n${YELLOW}4. Process a file directly...${NC}"
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "bucket": "file-parsing-uploads",
    "key": "uploads/sample_data.csv",
    "mappingSource": "default"
  }' \
  ${API_URL}/process
echo ""

echo -e "\n${GREEN}All tests completed!${NC}"