# File Parsing API with FastAPI

This is a FastAPI-based application for parsing different file formats (CSV, Excel, JSON, text) and mapping them to a standardized schema.

## Features

- Parses various file formats (CSV, Excel, JSON, text)
- Maps different source column names to standardized fields
- Stores parsed data in a PostgreSQL database
- Provides REST API endpoints for file upload and mapping configuration
- Containerized with Docker and Docker Compose

## Project Structure

```
file-parsing-api/
├── main.py              # Main FastAPI application
├── config.py            # Configuration settings
├── database.py          # Database connection setup
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose configuration
├── requirements.txt     # Python dependencies
├── uploads/             # Directory for uploaded files
├── sample_files/        # Sample test files
│   ├── sample_data.csv
│   ├── vendor1_data.csv
│   ├── sample_data.json
│   └── sample_data.txt
├── start.sh             # Setup and start script
├── test_api.sh          # API testing script
└── tests/               # Unit tests
    └── test_api.py      # API tests
```

## Getting Started

### Prerequisites

- Docker and Docker Compose

### Running the Application

1. Clone the repository:
```bash
git clone <repository-url>
cd file-parsing-api
```

2. Run the start script to create sample files and start the application:
```bash
chmod +x start.sh
./start.sh
```

3. Access the API documentation:
```
http://localhost:8000/docs
```

### Testing the API

Use the provided test script to test all endpoints:
```bash
chmod +x test_api.sh
./test_api.sh
```

Or test individual endpoints manually:

1. Add a mapping:
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
  http://localhost:8000/api/mappings
```

2. Upload a file:
```bash
curl -X POST \
  -F "file=@sample_files/sample_data.csv" \
  -F "source=default" \
  http://localhost:8000/api/upload
```

3. Get all mappings:
```bash
curl http://localhost:8000/api/mappings
```

4. Check API health:
```bash
curl http://localhost:8000/health
```

## Running Tests

Run the tests inside the Docker container:
```bash
docker-compose exec api pytest
```

Or run them locally:
```bash
pip install -r requirements.txt
pytest
```

## Customizing Field Mappings

Field mappings are defined in `config.py`. Each mapping configuration has:
- A name (e.g., "default", "vendor1")
- A dictionary mapping target fields to possible source field names

Add new mappings through the API or by modifying `config.py`.

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `UPLOAD_DIR`: Directory for temporary file storage
- `PORT`: Port for the FastAPI application

## Development

To run the application in development mode:
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```


# Setup Commands for FastAPI File Parsing API

# 1. Create Project Directory
mkdir -p file-parsing-api
cd file-parsing-api

# 2. Create Necessary Files
# Create all Python files (main.py, config.py, database.py, models.py, schemas.py)
# Create Docker files (Dockerfile, docker-compose.yml)
# Create requirements.txt
# Create test files and scripts (start.sh, test_api.sh)

# 3. Create Required Directories
mkdir -p uploads
mkdir -p sample_files
mkdir -p tests

# 4. Create Sample Files
# Populate sample_files directory with test data

# 5. Make Scripts Executable
chmod +x start.sh
chmod +x test_api.sh

# 6. Start the Application
./start.sh
# Or directly with docker-compose
docker-compose up --build

# 7. Run API Tests
./test_api.sh

# 8. Run Unit Tests
docker-compose exec api pytest

# 9. Stop the Application
docker-compose down

# 10. Clean Up (if needed)
docker-compose down -v  # Remove volumes too

# Individual API Testing Commands
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
      "auth_id": ["client_code"]
    }
  }' \
  http://localhost:8000/api/mappings

# Upload a file
curl -X POST \
  -F "file=@sample_files/sample_data.csv" \
  -F "source=default" \
  http://localhost:8000/api/upload

# Get all mappings
curl http://localhost:8000/api/mappings

# Check API health
curl http://localhost:8000/health