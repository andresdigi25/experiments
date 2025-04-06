#!/bin/bash
#### the commands htat worked for me are:
#### docker build -t excel-generator .       
### docker run --rm -v $(pwd)/output:/output excel-generator
# Build the Docker image
docker build -t excel-generator .

# Run the Docker container
docker run --name excel-generator-container excel-generator

# Copy the file from the Docker container to the host machine
docker cp excel-generator-container:/output/large_file.xlsx ./large_file.xlsx

# Stop and remove the Docker container
docker rm excel-generator-container