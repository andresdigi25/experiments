# Project Structure
# 
# /tracing-demo/
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
opentelemetry-api==1.15.0
opentelemetry-sdk==1.15.0
opentelemetry-instrumentation-fastapi==0.36b0
opentelemetry-exporter-otlp==1.15.0
opentelemetry-instrumentation-httpx==0.36b0

# docker-compose.yml
version: '3.8'

services:
  # LocalStack for AWS services
  localstack:
    image: localstack/localstack:latest
    ports:
      - "4566:4566"
    environment:
      - SERVICES=cloudwatch,xray
      - DEBUG=1
      - DATA_DIR=/tmp/localstack/data
    volumes:
      - ./init-aws.sh:/docker-entrypoint-initaws.d/init-aws.sh
  
  # Jaeger for trace visualization
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # UI
      - "4317:4317"    # OTLP gRPC
      - "4318:4318"    # OTLP HTTP
  
  # Our microservices
  service-user:
    build: ./service_user
    ports:
      - "8001:8000"
    environment:
      - ORDER_SERVICE_URL=http://service-order:8000
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
      - SERVICE_NAME=user-service
    depends_on:
      - jaeger
      - localstack
  
  service-order:
    build: ./service_order
    ports:
      - "8002:8000"
    environment:
      - PRODUCT_SERVICE_URL=http://service-product:8000
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
      - SERVICE_NAME=order-service
    depends_on:
      - jaeger
      - localstack
  
  service-product:
    build: ./service_product
    ports:
      - "8003:8000"
    environment:
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
      - SERVICE_NAME=product-service
    depends_on:
      - jaeger
      - localstack

# init-aws.sh
#!/bin/bash
awslocal cloudwatch create-log-group --log-group-name /microservices
awslocal cloudwatch create-log-stream --log-group-name /microservices --log-stream-name user-service
awslocal cloudwatch create-log-stream --log-group-name /microservices --log-stream-name order-service
awslocal cloudwatch create-log-stream --log-group-name /microservices --log-stream-name product-service

# service_user/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY service_user/main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# service_order/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY service_order/main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# service_product/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY service_product/main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# service_user/main.py
import os
import logging
import httpx
import json
import uuid
from fastapi import FastAPI, HTTPException, Request
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
service_name = os.getenv("SERVICE_NAME", "user-service")
order_service_url = os.getenv("ORDER_SERVICE_URL", "http://localhost:8002")

# Setup OpenTelemetry
resource = Resource(attributes={
    SERVICE_NAME: service_name
})

tracer_provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter()
span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)
trace.set_tracer_provider(tracer_provider)

tracer = trace.get_tracer(__name__)

# Create FastAPI app
app = FastAPI(title="User Service")
HTTPXInstrumentor().instrument()
FastAPIInstrumentor.instrument_app(app)

# Sample user database
users = {
    "1": {"id": "1", "name": "John Doe", "email": "john@example.com"},
    "2": {"id": "2", "name": "Jane Smith", "email": "jane@example.com"},
}

@app.get("/")
async def root():
    return {"message": "User Service is running"}

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    with tracer.start_as_current_span("get_user_data") as span:
        span.set_attribute("user.id", user_id)
        logger.info(f"Fetching user with ID: {user_id}")
        return users[user_id]

@app.get("/users/{user_id}/orders")
async def get_user_orders(user_id: str):
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")

    with tracer.start_as_current_span("get_user_orders") as span:
        span.set_attribute("user.id", user_id)
        logger.info(f"Fetching orders for user: {user_id}")
        
        # Call Order Service to get user's orders
        async with httpx.AsyncClient() as client:
            try:
                # Add correlation ID to the request
                correlation_id = str(uuid.uuid4())
                logger.info(f"Correlation ID: {correlation_id}")
                span.set_attribute("correlation.id", correlation_id)

                headers = {"X-Correlation-ID": correlation_id}
                response = await client.get(f"{order_service_url}/users/{user_id}/orders", headers=headers)
                response.raise_for_status()
                
                orders = response.json()
                span.set_attribute("orders.count", len(orders))
                return {"user": users[user_id], "orders": orders}
            
            except httpx.HTTPStatusError as e:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                logger.error(f"Error fetching orders: {str(e)}")
                raise HTTPException(status_code=e.response.status_code, detail="Error fetching orders")
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                logger.error(f"Unexpected error: {str(e)}")
                raise HTTPException(status_code=500, detail="Internal server error")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Get or generate correlation ID
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    # Add correlation ID to the current span
    current_span = trace.get_current_span()
    current_span.set_attribute("correlation.id", correlation_id)
    
    # Log the request
    logger.info(f"Request to {request.url.path} with correlation ID: {correlation_id}")
    
    # Process the request
    response = await call_next(request)
    
    # Add correlation ID to response headers
    response.headers["X-Correlation-ID"] = correlation_id
    
    return response

# service_order/main.py
import os
import logging
import httpx
import uuid
from fastapi import FastAPI, HTTPException, Request
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
service_name = os.getenv("SERVICE_NAME", "order-service")
product_service_url = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8003")

# Setup OpenTelemetry
resource = Resource(attributes={
    SERVICE_NAME: service_name
})

tracer_provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter()
span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)
trace.set_tracer_provider(tracer_provider)

tracer = trace.get_tracer(__name__)

# Create FastAPI app
app = FastAPI(title="Order Service")
HTTPXInstrumentor().instrument()
FastAPIInstrumentor.instrument_app(app)

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
    return {"message": "Order Service is running"}

@app.get("/orders/{order_id}")
async def get_order(order_id: str, request: Request):
    # Extract the correlation ID from the request headers
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    with tracer.start_as_current_span("get_order_details") as span:
        span.set_attribute("order.id", order_id)
        span.set_attribute("correlation.id", correlation_id)
        
        logger.info(f"Fetching order with ID: {order_id}, correlation ID: {correlation_id}")
        
        # Find the order
        for user_id, user_orders in orders.items():
            for order in user_orders:
                if order["id"] == order_id:
                    return order
        
        span.set_attribute("error", True)
        span.set_attribute("error.message", "Order not found")
        raise HTTPException(status_code=404, detail="Order not found")

@app.get("/users/{user_id}/orders")
async def get_user_orders(user_id: str, request: Request):
    # Extract the correlation ID from the request headers
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    with tracer.start_as_current_span("list_user_orders") as span:
        span.set_attribute("user.id", user_id)
        span.set_attribute("correlation.id", correlation_id)
        
        logger.info(f"Fetching orders for user: {user_id}, correlation ID: {correlation_id}")
        
        if user_id not in orders:
            span.set_attribute("error", True)
            span.set_attribute("error.message", "No orders found for user")
            logger.warning(f"No orders found for user: {user_id}")
            return []
        
        user_orders = orders[user_id]
        span.set_attribute("orders.count", len(user_orders))
        
        # Enrich orders with product details
        enriched_orders = []
        async with httpx.AsyncClient() as client:
            for order in user_orders:
                product_id = order["product_id"]
                try:
                    # Forward the correlation ID
                    headers = {"X-Correlation-ID": correlation_id}
                    response = await client.get(f"{product_service_url}/products/{product_id}", headers=headers)
                    response.raise_for_status()
                    
                    product = response.json()
                    enriched_order = {**order, "product": product}
                    enriched_orders.append(enriched_order)
                    
                except Exception as e:
                    logger.error(f"Error fetching product {product_id}: {str(e)}")
                    # Add order without product details
                    enriched_orders.append(order)
        
        return enriched_orders

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Get or generate correlation ID
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    # Add correlation ID to the current span
    current_span = trace.get_current_span()
    current_span.set_attribute("correlation.id", correlation_id)
    
    # Log the request
    logger.info(f"Request to {request.url.path} with correlation ID: {correlation_id}")
    
    # Process the request
    response = await call_next(request)
    
    # Add correlation ID to response headers
    response.headers["X-Correlation-ID"] = correlation_id
    
    return response

# service_product/main.py
import os
import logging
import random
import time
import uuid
from fastapi import FastAPI, HTTPException, Request
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
service_name = os.getenv("SERVICE_NAME", "product-service")

# Setup OpenTelemetry
resource = Resource(attributes={
    SERVICE_NAME: service_name
})

tracer_provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter()
span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)
trace.set_tracer_provider(tracer_provider)

tracer = trace.get_tracer(__name__)

# Create FastAPI app
app = FastAPI(title="Product Service")
FastAPIInstrumentor.instrument_app(app)

# Sample product database
products = {
    "1": {"id": "1", "name": "Laptop", "price": 1299.99, "inventory": 45},
    "2": {"id": "2", "name": "Smartphone", "price": 799.99, "inventory": 32},
    "3": {"id": "3", "name": "Headphones", "price": 199.99, "inventory": 78}
}

@app.get("/")
async def root():
    return {"message": "Product Service is running"}

@app.get("/products/{product_id}")
async def get_product(product_id: str, request: Request):
    # Extract the correlation ID from the request headers
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    with tracer.start_as_current_span("get_product_details") as span:
        span.set_attribute("product.id", product_id)
        span.set_attribute("correlation.id", correlation_id)
        
        logger.info(f"Fetching product with ID: {product_id}, correlation ID: {correlation_id}")
        
        # Simulate occasional latency for tracing demonstration
        if random.random() < 0.3:
            delay = random.uniform(0.5, 2.0)
            logger.info(f"Simulating latency of {delay:.2f}s for product {product_id}")
            span.set_attribute("simulated.latency", delay)
            time.sleep(delay)
        
        if product_id not in products:
            span.set_attribute("error", True)
            span.set_attribute("error.message", "Product not found")
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Simulate occasional inventory check latency
        with tracer.start_as_current_span("check_inventory") as inventory_span:
            inventory_span.set_attribute("product.id", product_id)
            inventory_span.set_attribute("inventory.level", products[product_id]["inventory"])
            
            if random.random() < 0.2:
                delay = random.uniform(0.3, 1.0)
                logger.info(f"Simulating inventory check latency of {delay:.2f}s")
                inventory_span.set_attribute("simulated.latency", delay)
                time.sleep(delay)
        
        return products[product_id]

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Get or generate correlation ID
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    # Add correlation ID to the current span
    current_span = trace.get_current_span()
    current_span.set_attribute("correlation.id", correlation_id)
    
    # Log the request
    logger.info(f"Request to {request.url.path} with correlation ID: {correlation_id}")
    
    # Process the request
    response = await call_next(request)
    
    # Add correlation ID to response headers
    response.headers["X-Correlation-ID"] = correlation_id
    
    return response