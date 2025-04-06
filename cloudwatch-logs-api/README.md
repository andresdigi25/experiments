# CloudWatch Logs Dashboard API

A FastAPI backend for querying and analyzing AWS CloudWatch logs from multiple services.

## Features

- Query log groups and log streams from CloudWatch
- Fetch log events with filtering capabilities
- Run CloudWatch Logs Insights queries
- Join query results across multiple services/log groups
- Async processing for improved performance

## Requirements

- Python 3.9+
- AWS credentials with CloudWatch Logs access
- Docker (optional, for containerized deployment)

## Setup

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/cloudwatch-logs-dashboard.git
   cd cloudwatch-logs-dashboard
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on the sample:
   ```bash
   cp sample.env .env
   ```

5. Edit the `.env` file with your AWS credentials and settings.

6. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker Deployment

1. Build and start the container:
   ```bash
   docker-compose up -d
   ```

2. View logs:
   ```bash
   docker-compose logs -f
   ```

## API Endpoints

Once the application is running, you can access:

- API documentation: http://localhost:8000/docs
- Alternative API documentation: http://localhost:8000/redoc
- Health check: http://localhost:8000/

### Main Endpoints

- **GET /api/log-groups** - List CloudWatch log groups
- **GET /api/log-streams/{log_group_name}** - List log streams in a log group
- **GET /api/logs/{log_group_name}** - Get log events from a log group
- **GET/POST /api/query** - Run a CloudWatch Logs Insights query
- **GET/POST /api/join-query** - Join logs across multiple services

## CloudWatch Logs Insights Query Examples

Here are some useful query examples for the query endpoints:

### Error Counts by Time

```
filter @message like "ERROR"
| stats count(*) as errorCount by bin(1h) as time
| sort time asc
```

### Response Time Statistics

```
filter responseTime != ""
| stats avg(responseTime) as avgResponseTime, min(responseTime) as minResponseTime, max(responseTime) as maxResponseTime by bin(1h) as time
| sort time asc
```

### Top Endpoints by Request Count

```
filter httpMethod != "" and path != ""
| stats count(*) as requestCount by httpMethod, path
| sort requestCount desc
| limit 10
```

### Error Distribution by Type

```
filter level="ERROR" or level="error"
| parse @message /Exception: (?<exceptionType>[^:]+)/ 
| stats count(*) as errorCount by exceptionType
| sort errorCount desc
```

## Joining Logs Example

To join logs from multiple services based on a request ID:

```json
{
  "services": ["api", "auth", "payment"],
  "log_groups": ["/aws/lambda/api-service", "/aws/lambda/auth-service", "/aws/lambda/payment-service"],
  "query_string": "filter requestId != \"\" | fields @timestamp, @message, requestId, level",
  "join_field": "requestId",
  "start_time": "2023-03-01T00:00:00Z",
  "end_time": "2023-03-02T00:00:00Z"
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| AWS_REGION | AWS region for CloudWatch | us-east-1 |
| AWS_ACCESS_KEY_ID | AWS access key | - |
| AWS_SECRET_ACCESS_KEY | AWS secret key | - |
| USE_AWS_INSTANCE_PROFILE | Use instance profile for AWS auth | False |
| LOG_LEVEL | Application logging level | INFO |
| MAX_LOGS_RESULTS | Maximum number of logs to return | 1000 |
| MAX_QUERY_DURATION_SECONDS | Max time for query execution | 300 |
| CORS_ORIGINS | Allowed origins for CORS | ["http://localhost:4200"] |

## License

MIT