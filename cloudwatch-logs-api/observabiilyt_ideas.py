# Project Structure
#
# /simple-tracing-demo/
# ├── docker-compose.yml
# ├── requirements.txt
# ├── service_product/
# │   ├── Dockerfile
# │   └── main.py
# ├── service_order/
# │   ├── Dockerfile
# │   └── main.py
# └── service_user/
#     ├── Dockerfile
#     └── main.py

# requirements.txt
fastapi==0.95.0
uvicorn==0.21.1
httpx==0.24.0
python-json-logger==2.0.7
boto3==1.26.115

# docker-compose.yml
version: '3.8'

services:
  # LocalStack for AWS services
  localstack:
    image: localstack/localstack:latest
    ports:
      - "4566:4566"
    environment:
      - SERVICES=cloudwatch,s3
      - DEBUG=1
      - DATA_DIR=/tmp/localstack/data
    volumes:
      - ./init-aws.sh:/docker-entrypoint-initaws.d/init-aws.sh

  # Elasticsearch for log aggregation
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - esdata:/usr/share/elasticsearch/data

  # Kibana for log visualization
  kibana:
    image: docker.elastic.co/kibana/kibana:7.17.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

  # Filebeat to ship logs to Elasticsearch
  filebeat:
    image: docker.elastic.co/beats/filebeat:7.17.0
    volumes:
      - ./filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - ./logs:/var/log/services:ro
    depends_on:
      - elasticsearch
      - kibana

  # Our microservices
  service-user:
    build: ./service_user
    ports:
      - "8001:8000"
    environment:
      - ORDER_SERVICE_URL=http://service-order:8000
      - AWS_ENDPOINT_URL=http://localstack:4566
      - SERVICE_NAME=user-service
      - LOG_FILE=/var/log/services/user-service.log
    volumes:
      - ./logs:/var/log/services
    depends_on:
      - localstack

  service-order:
    build: ./service_order
    ports:
      - "8002:8000"
    environment:
      - PRODUCT_SERVICE_URL=http://service-product:8000
      - AWS_ENDPOINT_URL=http://localstack:4566
      - SERVICE_NAME=order-service
      - LOG_FILE=/var/log/services/order-service.log
    volumes:
      - ./logs:/var/log/services
    depends_on:
      - localstack

  service-product:
    build: ./service_product
    ports:
      - "8003:8000"
    environment:
      - AWS_ENDPOINT_URL=http://localstack:4566
      - SERVICE_NAME=product-service
      - LOG_FILE=/var/log/services/product-service.log
    volumes:
      - ./logs:/var/log/services
    depends_on:
      - localstack

volumes:
  esdata:

# init-aws.sh
#!/bin/bash
awslocal cloudwatch create-log-group --log-group-name /microservices
awslocal cloudwatch create-log-stream --log-group-name /microservices --log-stream-name user-service
awslocal cloudwatch create-log-stream --log-group-name /microservices --log-stream-name order-service
awslocal cloudwatch create-log-stream --log-group-name /microservices --log-stream-name product-service

mkdir -p /tmp/localstack/data/logs

# filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/services/*.log
    json.keys_under_root: true
    json.add_error_key: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]

setup.kibana:
  host: "kibana:5601"

setup.dashboards.enabled: true

# service_user/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY service_user/main.py .
RUN mkdir -p /var/log/services

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# service_order/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY service_order/main.py .
RUN mkdir -p /var/log/services

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# service_product/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY service_product/main.py .
RUN mkdir -p /var/log/services

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# service_user/main.py
import os
import logging
import httpx
import json
import uuid
import time
import boto3
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pythonjsonlogger import jsonlogger
import datetime

# Get environment variables
service_name = os.getenv("SERVICE_NAME", "user-service")
order_service_url = os.getenv("ORDER_SERVICE_URL", "http://localhost:8002")
aws_endpoint_url = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
log_file = os.getenv("LOG_FILE", f"/var/log/services/{service_name}.log")

# Setup JSON logging
logger = logging.getLogger(service_name)
logger.setLevel(logging.INFO)

# File handler for JSON logs
os.makedirs(os.path.dirname(log_file), exist_ok=True)
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)

# Console handler for debugging
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# JSON formatter
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['service'] = service_name
        log_record['timestamp'] = datetime.datetime.now().isoformat()
        if not log_record.get('severity'):
            log_record['severity'] = record.levelname

formatter = CustomJsonFormatter('%(timestamp)s %(service)s %(severity)s %(message)s %(correlation_id)s %(duration_ms)s %(span)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Setup CloudWatch client
cloudwatch = boto3.client('logs', endpoint_url=aws_endpoint_url, 
                         region_name='us-east-1',
                         aws_access_key_id='test',
                         aws_secret_access_key='test')

# Helper function for CloudWatch Logs
def send_to_cloudwatch(log_event, correlation_id):
    try:
        timestamp = int(time.time() * 1000)
        cloudwatch.put_log_events(
            logGroupName='/microservices',
            logStreamName=service_name,
            logEvents=[
                {
                    'timestamp': timestamp,
                    'message': json.dumps({**log_event, 'correlation_id': correlation_id})
                }
            ]
        )
    except Exception as e:
        logger.error(f"Failed to send logs to CloudWatch: {str(e)}", 
                    extra={'correlation_id': correlation_id, 'span': 'cloudwatch_error'})

# Create FastAPI app
app = FastAPI(title="User Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample user database
users = {
    "1": {"id": "1", "name": "John Doe", "email": "john@example.com"},
    "2": {"id": "2", "name": "Jane Smith", "email": "jane@example.com"},
}

@app.get("/")
async def root():
    return {"message": f"{service_name} is running"}

class TimingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        start_time = time.time()
        
        # Create custom send function to capture response
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Calculate duration when the response headers are sent
                duration_ms = (time.time() - start_time) * 1000
                
                # Get the request from the scope
                request = scope.get("app_request", {})
                
                # Log the response timing
                correlation_id = request.headers.get("X-Correlation-ID", "unknown")
                path = scope.get("path", "unknown")
                method = scope.get("method", "unknown")
                
                logger.info(
                    f"Response sent for {method} {path}",
                    extra={
                        'correlation_id': correlation_id,
                        'duration_ms': f"{duration_ms:.2f}",
                        'span': 'http_response',
                        'status_code': message.get("status", 0)
                    }
                )
                
                # Send to CloudWatch
                send_to_cloudwatch({
                    'message': f"Response sent for {method} {path}",
                    'duration_ms': f"{duration_ms:.2f}",
                    'span': 'http_response',
                    'status_code': message.get("status", 0)
                }, correlation_id)
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)

app.add_middleware(TimingMiddleware)

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    # Store request in scope for the timing middleware
    request.scope["app_request"] = request
    
    # Get or generate correlation ID
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    # Start timing
    start_time = time.time()
    
    # Log the request
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            'correlation_id': correlation_id,
            'span': 'http_request',
            'method': request.method,
            'path': request.url.path,
            'duration_ms': "0.00"
        }
    )
    
    # Send to CloudWatch
    send_to_cloudwatch({
        'message': f"Request started: {request.method} {request.url.path}",
        'span': 'http_request',
        'method': request.method,
        'path': request.url.path
    }, correlation_id)
    
    # Process the request
    response = await call_next(request)
    
    # Add correlation ID to response headers
    response.headers["X-Correlation-ID"] = correlation_id
    
    return response

@app.get("/users/{user_id}")
async def get_user(user_id: str, request: Request):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    # Start timing
    start_time = time.time()
    
    # Log the operation start
    logger.info(
        f"Fetching user with ID: {user_id}",
        extra={
            'correlation_id': correlation_id,
            'span': 'get_user',
            'user_id': user_id,
            'duration_ms': "0.00"
        }
    )
    
    # Check if user exists
    if user_id not in users:
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log the error
        logger.error(
            f"User not found: {user_id}",
            extra={
                'correlation_id': correlation_id,
                'span': 'get_user',
                'error': 'user_not_found',
                'user_id': user_id,
                'duration_ms': f"{duration_ms:.2f}"
            }
        )
        
        # Send to CloudWatch
        send_to_cloudwatch({
            'message': f"User not found: {user_id}",
            'span': 'get_user',
            'error': 'user_not_found',
            'user_id': user_id,
            'duration_ms': f"{duration_ms:.2f}"
        }, correlation_id)
        
        raise HTTPException(status_code=404, detail="User not found")
    
    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000
    
    # Log the successful operation
    logger.info(
        f"User retrieved successfully: {user_id}",
        extra={
            'correlation_id': correlation_id,
            'span': 'get_user',
            'user_id': user_id,
            'duration_ms': f"{duration_ms:.2f}"
        }
    )
    
    # Send to CloudWatch
    send_to_cloudwatch({
        'message': f"User retrieved successfully: {user_id}",
        'span': 'get_user',
        'user_id': user_id,
        'duration_ms': f"{duration_ms:.2f}"
    }, correlation_id)
    
    return users[user_id]

@app.get("/users/{user_id}/orders")
async def get_user_orders(user_id: str, request: Request):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    # Start timing
    start_time = time.time()
    
    # Log the operation start
    logger.info(
        f"Fetching orders for user: {user_id}",
        extra={
            'correlation_id': correlation_id,
            'span': 'get_user_orders',
            'user_id': user_id,
            'duration_ms': "0.00"
        }
    )
    
    # Check if user exists
    if user_id not in users:
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log the error
        logger.error(
            f"User not found: {user_id}",
            extra={
                'correlation_id': correlation_id,
                'span': 'get_user_orders',
                'error': 'user_not_found',
                'user_id': user_id,
                'duration_ms': f"{duration_ms:.2f}"
            }
        )
        
        # Send to CloudWatch
        send_to_cloudwatch({
            'message': f"User not found: {user_id}",
            'span': 'get_user_orders',
            'error': 'user_not_found',
            'user_id': user_id,
            'duration_ms': f"{duration_ms:.2f}"
        }, correlation_id)
        
        raise HTTPException(status_code=404, detail="User not found")
    
    # Call Order Service to get user's orders
    call_start_time = time.time()
    
    logger.info(
        f"Calling order service for user: {user_id}",
        extra={
            'correlation_id': correlation_id,
            'span': 'call_order_service',
            'user_id': user_id,
            'duration_ms': "0.00"
        }
    )
    
    async with httpx.AsyncClient() as client:
        try:
            # Forward the correlation ID
            headers = {"X-Correlation-ID": correlation_id}
            response = await client.get(f"{order_service_url}/users/{user_id}/orders", headers=headers)
            
            # Calculate call duration
            call_duration_ms = (time.time() - call_start_time) * 1000
            
            logger.info(
                f"Order service response received: {response.status_code}",
                extra={
                    'correlation_id': correlation_id,
                    'span': 'call_order_service',
                    'status_code': response.status_code,
                    'duration_ms': f"{call_duration_ms:.2f}"
                }
            )
            
            # Send to CloudWatch
            send_to_cloudwatch({
                'message': f"Order service response received: {response.status_code}",
                'span': 'call_order_service',
                'status_code': response.status_code,
                'duration_ms': f"{call_duration_ms:.2f}"
            }, correlation_id)
            
            response.raise_for_status()
            orders = response.json()
            
            # Calculate total duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the successful operation
            logger.info(
                f"Orders retrieved successfully for user: {user_id}",
                extra={
                    'correlation_id': correlation_id,
                    'span': 'get_user_orders',
                    'user_id': user_id,
                    'order_count': len(orders),
                    'duration_ms': f"{duration_ms:.2f}"
                }
            )
            
            # Send to CloudWatch
            send_to_cloudwatch({
                'message': f"Orders retrieved successfully for user: {user_id}",
                'span': 'get_user_orders',
                'user_id': user_id,
                'order_count': len(orders),
                'duration_ms': f"{duration_ms:.2f}"
            }, correlation_id)
            
            return {"user": users[user_id], "orders": orders}
            
        except httpx.HTTPStatusError as e:
            # Calculate total duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the error
            logger.error(
                f"Error fetching orders: {str(e)}",
                extra={
                    'correlation_id': correlation_id,
                    'span': 'get_user_orders',
                    'error': 'order_service_error',
                    'status_code': e.response.status_code,
                    'error_detail': str(e),
                    'duration_ms': f"{duration_ms:.2f}"
                }
            )
            
            # Send to CloudWatch
            send_to_cloudwatch({
                'message': f"Error fetching orders: {str(e)}",
                'span': 'get_user_orders',
                'error': 'order_service_error',
                'status_code': e.response.status_code,
                'error_detail': str(e),
                'duration_ms': f"{duration_ms:.2f}"
            }, correlation_id)
            
            raise HTTPException(status_code=e.response.status_code, detail="Error fetching orders")
            
        except Exception as e:
            # Calculate total duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the error
            logger.error(
                f"Unexpected error: {str(e)}",
                extra={
                    'correlation_id': correlation_id,
                    'span': 'get_user_orders',
                    'error': 'unexpected_error',
                    'error_detail': str(e),
                    'duration_ms': f"{duration_ms:.2f}"
                }
            )
            
            # Send to CloudWatch
            send_to_cloudwatch({
                'message': f"Unexpected error: {str(e)}",
                'span': 'get_user_orders',
                'error': 'unexpected_error',
                'error_detail': str(e),
                'duration_ms': f"{duration_ms:.2f}"
            }, correlation_id)
            
            raise HTTPException(status_code=500, detail="Internal server error")

# service_order/main.py
import os
import logging
import httpx
import json
import uuid
import time
import boto3
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pythonjsonlogger import jsonlogger
import datetime

# Get environment variables
service_name = os.getenv("SERVICE_NAME", "order-service")
product_service_url = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8003")
aws_endpoint_url = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
log_file = os.getenv("LOG_FILE", f"/var/log/services/{service_name}.log")

# Setup JSON logging
logger = logging.getLogger(service_name)
logger.setLevel(logging.INFO)

# File handler for JSON logs
os.makedirs(os.path.dirname(log_file), exist_ok=True)
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)

# Console handler for debugging
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# JSON formatter
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['service'] = service_name
        log_record['timestamp'] = datetime.datetime.now().isoformat()
        if not log_record.get('severity'):
            log_record['severity'] = record.levelname

formatter = CustomJsonFormatter('%(timestamp)s %(service)s %(severity)s %(message)s %(correlation_id)s %(duration_ms)s %(span)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Setup CloudWatch client
cloudwatch = boto3.client('logs', endpoint_url=aws_endpoint_url, 
                         region_name='us-east-1',
                         aws_access_key_id='test',
                         aws_secret_access_key='test')

# Helper function for CloudWatch Logs
def send_to_cloudwatch(log_event, correlation_id):
    try:
        timestamp = int(time.time() * 1000)
        cloudwatch.put_log_events(
            logGroupName='/microservices',
            logStreamName=service_name,
            logEvents=[
                {
                    'timestamp': timestamp,
                    'message': json.dumps({**log_event, 'correlation_id': correlation_id})
                }
            ]
        )
    except Exception as e:
        logger.error(f"Failed to send logs to CloudWatch: {str(e)}", 
                    extra={'correlation_id': correlation_id, 'span': 'cloudwatch_error'})

# Create FastAPI app
app = FastAPI(title="Order Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample order database
orders = {
    "1": [
        {"id": "101", "product_id": "1", "quantity": 2, "status": "delivered"},
        {"id": "102", "product_id": "3", "quantity": 1, "status": "processing"}
    ],
    "2": [
        {"id": "103", "product_id": "2", "quantity": 5, "status": "shipped"}
    ]
}

@app.get("/")
async def root():
    return {"message": f"{service_name} is running"}

class TimingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        start_time = time.time()
        
        # Create custom send function to capture response
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Calculate duration when the response headers are sent
                duration_ms = (time.time() - start_time) * 1000
                
                # Get the request from the scope
                request = scope.get("app_request", {})
                
                # Log the response timing
                correlation_id = request.headers.get("X-Correlation-ID", "unknown")
                path = scope.get("path", "unknown")
                method = scope.get("method", "unknown")
                
                logger.info(
                    f"Response sent for {method} {path}",
                    extra={
                        'correlation_id': correlation_id,
                        'duration_ms': f"{duration_ms:.2f}",
                        'span': 'http_response',
                        'status_code': message.get("status", 0)
                    }
                )
                
                # Send to CloudWatch
                send_to_cloudwatch({
                    'message': f"Response sent for {method} {path}",
                    'duration_ms': f"{duration_ms:.2f}",
                    'span': 'http_response',
                    'status_code': message.get("status", 0)
                }, correlation_id)
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)

app.add_middleware(TimingMiddleware)

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    # Store request in scope for the timing middleware
    request.scope["app_request"] = request
    
    # Get or generate correlation ID
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    # Start timing
    start_time = time.time()
    
    # Log the request
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            'correlation_id': correlation_id,
            'span': 'http_request',
            'method': request.method,
            'path': request.url.path,
            'duration_ms': "0.00"
        }
    )
    
    # Send to CloudWatch
    send_to_cloudwatch({
        'message': f"Request started: {request.method} {request.url.path}",
        'span': 'http_request',
        'method': request.method,
        'path': request.url.path
    }, correlation_id)
    
    # Process the request
    response = await call_next(request)
    
    # Add correlation ID to response headers
    response.headers["X-Correlation-ID"] = correlation_id
    
    return response

@app.get("/orders/{order_id}")
async def get_order(order_id: str, request: Request):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    # Start timing
    start_time = time.time()
    
    # Log the operation start
    logger.info(
        f"Fetching order with ID: {order_id}",
        extra={
            'correlation_id': correlation_id,
            'span': 'get_order',
            'order_id': order_id,
            'duration_ms': "0.00"
        }
    )
    
    # Find the order
    found_order = None
    for user_id, user_orders in orders.items():
        for order in user_orders:
            if order["id"] == order_id:
                found_order = order
                break
        if found_order:
            break
    
    if not found_order:
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log the error
        logger.error(
            f"Order not found: {order_id}",
            extra={
                'correlation_id': correlation_id,
                'span': 'get_order',
                'error': 'order_not_found',
                'order_id': order_id,
                'duration_ms': f"{duration_ms:.2f}"
            }
        )
        
        # Send to CloudWatch
        send_to_cloudwatch({
            'message': f"Order not found: {order_id}",
            'span': 'get_order',
            'error': 'order_not_found',
            'order_id': order_id,
            'duration_ms': f"{duration_ms:.2f}"
        }, correlation_id)
        
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000
    
    # Log the successful operation
    logger.info(
        f"Order retrieved successfully: {order_id}",
        extra={
            'correlation_id': correlation_id,
            'span': 'get_order',
            'order_id': order_id,
            'status': found_order["status"],
            'duration_ms': f"{duration_ms:.2f}"
        }
    )
    
    # Send to CloudWatch
    send_to_cloudwatch({
        'message': f"Order retrieved successfully: {order_id}",
        'span': 'get_order',
        'order_id': order_id,
        'status': found_order["status"],
        'duration_ms': f"{duration_ms:.2f}"
    }, correlation_id)
    
    return found_order

@app.get("/users/{user_id}/orders")
async def get_user_orders(user_id: str, request: Request):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    # Start timing
    start_time = time.time()
    
    # Log the operation start
    logger.info(
        f"Fetching orders for user: {user_id}",
        extra={
            'correlation_id': correlation_id,
            'span': 'list_user_orders',
            'user_id': user_id,
            'duration_ms': "0.00"
        }
    )
    
    # Check if user has orders
    if user_id not in orders:
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log the info (not an error since empty results are valid)
        logger.info(
            f"No orders found for user: {user_id}",
            extra={
                'correlation_id': correlation_id,
                'span': 'list_user_orders',
                'user_id': user_id,
                'order_count': 0,
                'duration_ms': f"{duration_ms:.2f}"
            }
        )
        
        # Send to CloudWatch
        send_to_cloudwatch({
            'message': f"No orders found for user: {user_id}",
            'span': 'list_user_orders',
            'user_id': user_id,
            'order_count': 0,
            'duration_ms': f"{duration_ms:.2f}"
        }, correlation_id)
        
        return []
    
    user_orders = orders[user_id]
    
    # Enrich orders with product details
    enriched_orders = []
    
    for order in user_orders:
        product_id = order["product_id"]
        
        # Start timing for product service call
        call_start_time = time.time()
        
        logger.info(
            f"Calling product service for product: {product_id}",
            extra={
                'correlation_id': correlation_id,
                'span': 'call_product_service',
                'product_id': product_id,
                'order_id': order["id"],
                'duration_ms': "0.00"
            }
        )
        
        # Send to CloudWatch
        send_to_cloudwatch({
            'message': f"Calling product service for product: {product_id}",
            'span': 'call_product_service',
            'product_id': product_id,
            'order_id': order["id"]
        }, correlation_id)
        
        try:
            async with httpx.AsyncClient() as client:
                # Forward the correlation ID
                headers = {"X-Correlation-ID": correlation_id}
                response = await client.get(f"{product_service_url}/products/{product_id}", headers=headers)
                
                # Calculate call duration
                call_duration_ms = (time.time() - call_start_time) * 1000
                
                logger.info(
                    f"Product service response received: {response.status_code}",
                    extra={
                        'correlation_id': correlation_id,
                        'span': 'call_product_service',
                        'product_id': product_id,
                        'status_code': response.status_code,
                        'duration_ms': f"{call_duration_ms:.2f}"
                    }
                )
                
                # Send to CloudWatch
                send_to_cloudwatch({
                    'message': f"Product service response received: {response.status_code}",
                    'span': 'call_product_service',
                    'product_id': product_id,
                    'status_code': response.status_code,
                    'duration_ms': f"{call_duration_ms:.2f}"
                }, correlation_id)
                
                response.raise_for_status()
                product = response.json()
                
                # Add product details to order
                enriched_order = {**order, "product": product}
                enriched_orders.append(enriched_order)
                
        except Exception as e:
            # Calculate call duration
            call_duration_ms = (time.time() - call_start_time) * 1000
            
            # Log the error
            logger.error(
                f"Error fetching product {product_id}: {str(e)}",
                extra={
                    'correlation_id': correlation_id,
                    'span': 'call_product_service',
                    'product_id': product_id,
                    'error': 'product_service_error',
                    'error_detail': str(e),
                    'duration_ms': f"{call_duration_ms:.2f}"
                }
            )
            
            # Send to CloudWatch
            send_to_cloudwatch({
                'message': f"Error fetching product {product_id}: {str(e)}",
                'span': 'call_product_service',
                'product_id': product_id,
                'error': 'product_service_error',
                'error_detail': str(e),
                'duration_ms': f"{call_duration_ms:.2f}"
            }, correlation_id)
            
            # Add order without product details
            enriched_orders.append(order)
    
    # Calculate total duration
    duration_ms = (time.time() - start_time) * 1000
    
    # Log the successful operation
    logger.info(
        f"Orders retrieved and enriched for user: {user_id}",
        extra={
            'correlation_id': correlation_id,
            'span': 'list_user_orders',
            'user_id': user_id,
            'order_count': len(enriched_orders),
            'duration_ms': f"{duration_ms:.2f}"
        }
    )
    
    # Send to CloudWatch
    send_to_cloudwatch({
        'message': f"Orders retrieved and enriched for user: {user_id}",
        'span': 'list_user_orders',
        'user_id': user_id,
        'order_count': len(enriched_orders),
        'duration_ms': f"{duration_ms:.2f}"
    }, correlation_id)
    
    return enriched_orders