#!/bin/bash

# Stop execution if any command fails
set -e

echo "Setting up Jupyter environment for address matching model..."

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

# Build Jupyter Docker image
echo "Building Jupyter Docker image..."
docker build -t address-matching-jupyter -f Dockerfile.jupyter .

# Print instructions
echo "Starting Jupyter notebook server..."
echo "Note: This will expose Jupyter without a password for convenience. Do not use in production."
echo "After the container starts, open your browser and navigate to: http://localhost:8888"
echo "To stop the container, press Ctrl+C"

# Run Docker container with Jupyter
docker run --rm -it \
    -p 8888:8888 \
    -v "$(pwd)/output:/app/output" \
    -v "$(pwd)/model:/app/model" \
    -v "$(pwd):/app/workspace" \
    -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
    -e AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
    -e AWS_SESSION_TOKEN="$AWS_SESSION_TOKEN" \
    -e AWS_REGION="${AWS_REGION:-us-east-1}" \
    address-matching-jupyter