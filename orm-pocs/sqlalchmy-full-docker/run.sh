#!/bin/bash
set -e

echo "Running SQLAlchemy 2.0 Async PostgreSQL Demo with Docker"
echo "======================================================"

# Build and start containers
echo "Starting Docker containers..."
docker-compose up --build

echo "Demo completed."