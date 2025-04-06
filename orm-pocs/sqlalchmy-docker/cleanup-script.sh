#!/bin/bash
set -e

echo "Cleaning up SQLAlchemy 2.0 Async PostgreSQL Demo"
echo "==============================================="

# Stop and remove containers
echo "Stopping and removing PostgreSQL container..."
docker-compose down

# Ask if the user wants to remove volumes
read -p "Do you want to remove the PostgreSQL data volume? (y/n): " remove_volumes
if [[ $remove_volumes == "y" || $remove_volumes == "Y" ]]; then
    echo "Removing volumes..."
    docker-compose down -v
    echo "Volumes removed."
else
    echo "Volumes preserved."
fi

# Ask if the user wants to remove the virtual environment
read -p "Do you want to remove the Python virtual environment? (y/n): " remove_venv
if [[ $remove_venv == "y" || $remove_venv == "Y" ]]; then
    echo "Removing virtual environment..."
    rm -rf venv
    echo "Virtual environment removed."
else
    echo "Virtual environment preserved."
fi

echo "Cleanup completed."
