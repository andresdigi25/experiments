# CloudWatch Logs API Usage Guide

This guide provides examples of how to use the CloudWatch Logs API for querying and analyzing logs from multiple services.

## Prerequisites

- The API server is running and accessible at `http://localhost:8000`
- You have valid AWS credentials with access to CloudWatch Logs
- You can use tools like `curl`, Postman, or any HTTP client to make requests

## 1. Getting Log Groups

First, let's list available log groups:

```bash
curl -X GET "http://localhost:8000/api/log-groups"
```

You can filter log groups by prefix:

```bash
curl -X GET "http://localhost:8000/api/log-groups?prefix=/aws/lambda/"
```

## 2. Getting Log Streams

Once you have a log group, you can list its log streams:

```bash
curl -X GET "http://localhost:8000/api/log-streams/%2Faws%2Flambda%2Fmy-service"
```

Note: The `/` characters in the log group name are URL-encoded as `%2F`.

## 3. Fetching Logs

To get log events from a specific log group:

```bash
curl -X GET "http://localhost:8000/api/logs/%2Faws%2Flambda%2Fmy-service?limit=50"
```

You can add filters to narrow down the results:

```bash
curl -X GET "http://localhost:8000/api/logs/%2Faws%2Flambda%2Fmy-service?filter_pattern=ERROR&limit=50"
```

To filter logs by a specific time range:

```bash
curl -X GET "http://localhost:8000/api/logs/%2Faws%2Flambda%2Fmy-service?start_time=2023-03-01T00:00:00Z&end_time=2023-03-02T00:00:00Z"
```

## 4. Running Logs Insights Queries

CloudWatch Logs Insights provides a powerful query language. You can run queries via GET:

```bash
curl -X GET "http://localhost:8000/api/query?log_group_name=%2Faws%2Flambda%2Fmy-service&query_string=fields%20%40timestamp%2C%20%40message%20%7C%20limit%2020"
```

For more complex queries, use POST:

```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "log_group_name": "/aws/lambda/my-service",
    "service_name": "my-service",
    "query_string": "filter @message like \"ERROR\" | stats count(*) as errorCount by bin(1h) as time",
    "start_time": "2023-03-01T00:00:00Z",
    "end_time": "2023-03-02T00:00:00Z"
  }'
```

## 5. Joining Logs Across Services

To correlate logs from multiple services (e.g., by request ID):

```bash
curl -X POST "http://localhost:8000/api/join-query" \
  -H "Content-Type: application/json" \
  -d '{
    "services": ["api", "auth", "database"],
    "log_groups": ["/aws/lambda/api-service", "/aws/lambda/auth-service", "/aws/lambda/db-service"],
    "query_string": "filter requestId != \"\" | fields @timestamp, @message, requestId, level",
    "join_field": "requestId",
    "start_time": "2023-03-01T00:00:00Z",
    "end_time": "2023-03-02T00:00:00Z"
  }'
```

## Common CloudWatch Logs Insights Query Examples

### Count logs by level

```
stats count(*) by level
| sort count(*) desc
```

### Find slow API calls

```
filter duration > 1000
| sort by duration desc
| limit 100
```

### Error distribution over time

```
filter level = "ERROR"
| stats count(*) as errorCount by bin(15m) as timebin
| sort timebin asc
```

### Top error paths in an API

```
filter level = "ERROR" and path != ""
| stats count(*) as errorCount by path
| sort errorCount desc
| limit 10
```

### API request latency statistics

```
filter httpStatus >= 200
| stats 
    avg(duration) as avgLatency, 
    min(duration) as minLatency, 
    max(duration) as maxLatency, 
    pct(duration, 95) as p95Latency, 
    pct(duration, 99) as p99Latency 
  by path, httpMethod
| sort avgLatency desc
```

## Python Client Example

Here's how to use the API with Python:

```python
import requests
from datetime import datetime, timedelta

API_URL = "http://localhost:8000/api"

def get_log_groups():
    response = requests.get(f"{API_URL}/log-groups")
    return response.json()

def query_logs(log_group, query_string, hours=24):
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    payload = {
        "log_group_name": log_group,
        "query_string": query_string,
        "start_time": start_time.isoformat() + "Z",
        "end_time": end_time.isoformat() + "Z"
    }
    
    response = requests.post(f"{API_URL}/query", json=payload)
    return response.json()

def main():
    # Get log groups
    log_groups = get_log_groups()
    print(f"Found {len(log_groups)} log groups")
    
    # Query first log group for errors
    if log_groups:
        log_group = log_groups[0]["name"]
        query = 'filter @message like "ERROR" | stats count(*) as errorCount by bin(1h) as time'
        
        results = query_logs(log_group, query)
        print(f"Query results: {results}")

if __name__ == "__main__":
    main()
```

## Troubleshooting

### Common HTTP Status Codes

- **200**: Request successful
- **400**: Bad request (check parameters)
- **500**: Server error (check logs)

### Common Issues

1. **AWS Credentials**: Ensure your AWS credentials have permission to access CloudWatch Logs
2. **Query Timeout**: For complex queries on large log groups, increase the `MAX_QUERY_DURATION_SECONDS` setting
3. **URL Encoding**: Remember to URL-encode log group and stream names in GET requests
4. **Rate Limiting**: AWS may rate limit CloudWatch Logs API calls