# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script
COPY generate_excel2.py .

# Create an output directory
RUN mkdir /output

# Run the Python script
CMD ["python", "generate_excel2.py"]