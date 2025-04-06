#!/bin/bash
set -e

echo "Setting up SQLAlchemy 2.0 Async PostgreSQL Demo"
echo "==============================================="

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create Python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install required packages
echo "Installing required Python packages..."
pip install --upgrade pip
pip install sqlalchemy asyncpg greenlet

# Start PostgreSQL container
echo "Starting PostgreSQL container..."
docker-compose up -d

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
attempt=0
max_attempts=30
until docker exec sqlalchemy_demo_postgres pg_isready -U postgres -d sqlalchemy_demo -h localhost || [ $attempt -eq $max_attempts ]; do
    attempt=$((attempt+1))
    echo "Waiting for PostgreSQL to be ready... (attempt $attempt/$max_attempts)"
    sleep 1
done

if [ $attempt -eq $max_attempts ]; then
    echo "Error: PostgreSQL failed to start after $max_attempts attempts."
    echo "Please check the Docker logs using 'docker-compose logs postgres'."
    exit 1
fi

echo "PostgreSQL is ready!"
echo "Setup completed successfully."
echo ""
echo "To run the demo, use: ./run.sh"
echo "To stop the database, use: ./cleanup.sh"
