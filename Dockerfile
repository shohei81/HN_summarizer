# ---- Builder Stage ----
FROM --platform=linux/amd64 python:3.11-slim AS builder

# Set environment variables for the builder stage
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies into a target directory
# Using --no-cache-dir to keep the layer small
# Upgrading pip first is a good practice
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --target=/app/packages -r requirements.txt

# ---- Final Stage ----
FROM --platform=linux/amd64 gcr.io/distroless/python3-debian12:nonroot

# Set environment variables for the final stage
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Set PYTHONPATH to include the installed packages
ENV PYTHONPATH=/app/packages

WORKDIR /app

# Copy the installed Python packages from the builder stage
COPY --from=builder /app/packages /app/packages

# Copy the application code
COPY src/ ./src/
COPY config.yaml .
# If main.py were in the root, you would copy it like this:
# COPY main.py .

# User and permissions are handled by distroless:nonroot image (runs as non-root)

# Command to run the application
# Ensure main.py is in the src directory as expected.
# The distroless image has 'python3' (often symlinked as 'python') in its PATH.
CMD ["src/main.py", "--config", "config.yaml", "--debug"]
