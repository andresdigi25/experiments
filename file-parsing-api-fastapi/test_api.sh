#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Testing FastAPI File Parsing API${NC}"
echo "---------------------------------------------"

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
  http://localhost:8000/api/mappings
echo ""

# 2. Test with standard CSV file
echo -e "\n${YELLOW}2. Testing with standard CSV file...${NC}"
curl -X POST \
  -F "file=@sample_files/sample_data.csv" \
  -F "source=default" \
  http://localhost:8000/api/upload
echo ""

# 3. Test with vendor1 CSV file
echo -e "\n${YELLOW}3. Testing with vendor1 CSV file...${NC}"
curl -X POST \
  -F "file=@sample_files/vendor1_data.csv" \
  -F "source=vendor1" \
  http://localhost:8000/api/upload
echo ""

# 4. Test with standard JSON file
echo -e "\n${YELLOW}4. Testing with standard JSON file...${NC}"
curl -X POST \
  -F "file=@sample_files/sample_data.json" \
  -F "source=default" \
  http://localhost:8000/api/upload
echo ""

# 5. Test with text file
echo -e "\n${YELLOW}5. Testing with text file...${NC}"
curl -X POST \
  -F "file=@sample_files/sample_data.txt" \
  -F "source=default" \
  http://localhost:8000/api/upload
echo ""

# 6. Get all mapping configurations
echo -e "\n${YELLOW}6. Getting all mapping configurations...${NC}"
curl http://localhost:8000/api/mappings
echo ""

# 7. Test health check endpoint
echo -e "\n${YELLOW}7. Testing health check endpoint...${NC}"
curl http://localhost:8000/health
echo ""

echo -e "\n${GREEN}All tests completed!${NC}"