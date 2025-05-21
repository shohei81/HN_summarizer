# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies that might be needed by Python packages
# (Example: RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*)
# For now, we'll assume no extra system packages are needed beyond what's in python:3.10-slim

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY src/ ./src/
COPY config.yaml .
# If main.py is in the root and not in src, it should also be copied:
# COPY main.py . 
# Based on previous file listings, main.py is in src, so ./src/ covers it.

# Command to run the application
# Ensure main.py is in the src directory as expected.
CMD ["python", "src/main.py", "--config", "config.yaml", "--debug"]
