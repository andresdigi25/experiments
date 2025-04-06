# Option 1: Use the start script which creates sample files and starts the application
./start.sh

# Option 2: Run with Docker Compose directly
docker-compose up --build

# Run the test script to test all sample file types
./test_api.sh

# Or test individual endpoints manually:

# Add a mapping
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
      "authId": ["client_code"]
    }
  }' \
  http://localhost:3000/api/mappings

# Upload a file
curl -X POST -F "file=@sample_files/sample_data.csv" -F "source=default" http://localhost:3000/api/upload

# Get all mappings
curl http://localhost:3000/api/mappings


# Stop the running containers
docker-compose down

# If you want to remove all data (including database volumes)
docker-compose down -v


# Install dependencies
npm install

# Run the application in development mode
npm run dev