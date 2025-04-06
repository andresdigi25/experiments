#!/bin/bash
set -e

echo "Running SQLAlchemy 2.0 Async PostgreSQL Demo"
echo "==========================================="

# Check if the virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Check if PostgreSQL container is running
if ! docker ps | grep -q sqlalchemy_demo_postgres; then
    echo "Error: PostgreSQL container is not running. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Run the async SQLAlchemy demo
echo "Running async demo..."
python async_sqlalchemy_demo.py

echo "Demo completed."
