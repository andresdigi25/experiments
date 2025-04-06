import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

from main import app
from schemas import LogGroup

client = TestClient(app)

@pytest.fixture
def mock_log_groups():
    return [
        LogGroup(
            name="/aws/lambda/service1",
            arn="arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/service1:*",
            creation_time=1615123456789,
            retention_in_days=14,
            metric_filter_count=0
        ),
        LogGroup(
            name="/aws/lambda/service2",
            arn="arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/service2:*",
            creation_time=1615123456789,
            retention_in_days=14,
            metric_filter_count=0
        )
    ]

@patch("app.services.logs_service.get_log_groups")
def test_list_log_groups(mock_get_log_groups, mock_log_groups):
    # Setup mock
    mock_get_log_groups.return_value = mock_log_groups
    
    # Make request
    response = client.get("/api/log-groups")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "/aws/lambda/service1"
    assert data[1]["name"] == "/aws/lambda/service2"
    
    # Verify mock was called correctly
    mock_get_log_groups.assert_called_once_with(prefix=None, limit=50)

@patch("app.services.logs_service.get_log_groups")
def test_list_log_groups_with_prefix(mock_get_log_groups, mock_log_groups):
    # Setup mock with filtered data
    filtered_groups = [group for group in mock_log_groups if "service1" in group.name]
    mock_get_log_groups.return_value = filtered_groups
    
    # Make request
    response = client.get("/api/log-groups?prefix=/aws/lambda/service1")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "/aws/lambda/service1"
    
    # Verify mock was called correctly
    mock_get_log_groups.assert_called_once_with(prefix="/aws/lambda/service1", limit=50)

@patch("app.services.logs_service.get_log_groups")
def test_list_log_groups_error(mock_get_log_groups):
    # Setup mock to raise exception
    mock_get_log_groups.side_effect = Exception("AWS API error")
    
    # Make request
    response = client.get("/api/log-groups")
    
    # Check response
    assert response.status_code == 500
    assert "Error fetching log groups" in response.json()["detail"]