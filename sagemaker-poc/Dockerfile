FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your address matching script
COPY address_matching.py .

# Create directories for model artifacts
RUN mkdir -p model/model model/code

# Set the entry point to run the script with Python
ENTRYPOINT ["python", "address_matching.py"]