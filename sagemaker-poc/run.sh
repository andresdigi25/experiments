#!/bin/bash

# Stop execution if any command fails
set -e

echo "Setting up environment to run address matching model..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Create directory for output files
mkdir -p output

# Check if address_matching.py exists
if [ ! -f address_matching.py ]; then
    echo "Error: address_matching.py file not found in current directory."
    echo "Please make sure the file is in the current directory and try again."
    exit 1
fi

# Build Docker image
echo "Building Docker image..."
docker build -t address-matching .

# Run Docker container
echo "Running address matching script in Docker container..."
docker run -v "$(pwd)/output:/app/output" \
    -v "$(pwd)/model:/app/model" \
    -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
    -e AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
    -e AWS_SESSION_TOKEN="$AWS_SESSION_TOKEN" \
    -e AWS_REGION="${AWS_REGION:-us-east-1}" \
    address-matching

echo "Script execution completed! Check the 'output' directory for results."