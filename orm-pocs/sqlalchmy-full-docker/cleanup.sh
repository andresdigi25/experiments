#!/bin/bash
set -e

echo "Cleaning up SQLAlchemy 2.0 Async PostgreSQL Demo"
echo "==============================================="

# Stop and remove containers
echo "Stopping and removing containers..."
docker-compose down

# Ask if the user wants to remove volumes
read -p "Do you want to remove the PostgreSQL data volume? (y/n): " remove_volumes
if [[ $remove_volumes == "y" || $remove_volumes == "Y" ]]; then
    echo "Removing volumes..."
    docker-compose down -v
    docker volume prune -f
    echo "Volumes removed."
else
    echo "Volumes preserved."
fi

echo "Cleanup completed."