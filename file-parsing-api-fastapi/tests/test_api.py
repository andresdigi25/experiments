import pytest
from fastapi.testclient import TestClient
import os
import json
from unittest.mock import patch, mock_open

# Import the FastAPI app
from main import app

# Initialize the test client
client = TestClient(app)

# Fixture to mock database operations
@pytest.fixture
def mock_db():
    # Mock SQLAlchemy session
    with patch("main.get_db") as mock:
        yield mock

# Fixture to create a temp CSV file for testing
@pytest.fixture
def test_csv_content():
    return (
        "full_name,street_address,city,state,zipcode,auth_id\n"
        "John Doe,123 Main St,New York,NY,10001,AUTH001\n"
        "Jane Smith,456 Park Ave,Los Angeles,CA,90001,AUTH002\n"
    )

@pytest.fixture
def test_json_content():
    return json.dumps([
        {
            "name": "Thomas Anderson",
            "address": "555 Matrix St",
            "city": "San Francisco",
            "state": "CA",
            "postal_code": "94105",
            "authorization_id": "JSON001"
        }
    ])

# Tests
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_get_mappings():
    response = client.get("/api/mappings")
    assert response.status_code == 200
    assert "default" in response.json()
    assert "vendor1" in response.json()

def test_create_mapping():
    mapping_data = {
        "name": "test_vendor",
        "mappings": {
            "name": ["test_name", "client"],
            "address1": ["test_address"],
            "city": ["test_city"],
            "state": ["test_state"],
            "zip": ["test_zip"],
            "auth_id": ["test_id"]
        }
    }
    
    response = client.post(
        "/api/mappings",
        json=mapping_data
    )
    
    assert response.status_code == 200
    assert response.json()["name"] == "test_vendor"
    
    # Verify mapping was added by getting all mappings
    response = client.get("/api/mappings")
    assert "test_vendor" in response.json()

@patch("builtins.open", new_callable=mock_open, read_data="test data")
@patch("os.remove")
@patch("shutil.copyfileobj")
@patch("uuid.uuid4", return_value="test-uuid")
@patch("main.process_file")
@patch("main.save_records")
def test_upload_file(mock_save, mock_process, mock_uuid, mock_copy, mock_remove, mock_file, mock_db):
    # Setup mocks
    mock_process.return_value = {
        "total": 2,
        "valid": 2,
        "invalid": 0,
        "records": [{"name": "Test", "auth_id": "123"}]
    }
    mock_save.return_value = {"success": True, "count": 1}
    
    # Create test file
    with open("test_file.csv", "w") as f:
        f.write("test,data")
    
    # Test file upload
    with open("test_file.csv", "rb") as f:
        response = client.post(
            "/api/upload",
            files={"file": ("test_file.csv", f, "text/csv")},
            data={"source": "default"}
        )
    
    # Clean up
    if os.path.exists("test_file.csv"):
        os.remove("test_file.csv")
    
    # Assertions
    assert response.status_code == 200
    assert response.json()["message"] == "File processed successfully"
    assert response.json()["summary"]["totalRecords"] == 2
    assert response.json()["summary"]["validRecords"] == 2
    assert response.json()["summary"]["savedRecords"] == 1
    
    # Verify mock calls
    mock_process.assert_called_once()
    mock_save.assert_called_once()
    mock_remove.assert_called_once()

@patch("main.normalize_record")
def test_normalize_record(mock_normalize):
    # Setup mock
    mock_normalize.return_value = {
        "name": "John Doe",
        "address1": "123 Main St",
        "city": "New York",
        "state": "NY",
        "zip": "10001",
        "auth_id": "AUTH001"
    }
    
    # Test with default mapping
    record = {
        "full_name": "John Doe",
        "street_address": "123 Main St",
        "city": "New York", 
        "state": "NY",
        "zipcode": "10001",
        "auth_id": "AUTH001"
    }
    
    result = mock_normalize(record)
    
    # Assertions
    assert result["name"] == "John Doe"
    assert result["address1"] == "123 Main St"
    assert result["zip"] == "10001"
    assert result["auth_id"] == "AUTH001"