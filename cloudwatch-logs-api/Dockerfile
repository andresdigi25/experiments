FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /app/app

# Create a non-root user to run the application
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Expose the API port
EXPOSE 8000

# Set the command to start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]