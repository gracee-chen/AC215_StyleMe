FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY containers/training/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ /app/src/
COPY containers/training/entrypoint.sh /app/entrypoint.sh

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Set environment variables
ENV PYTHONPATH=/app/src
ENV DATA_DIR=/app/data
ENV EXPERIMENTS_DIR=/app/experiments
ENV CUDA_VISIBLE_DEVICES=0

# Create directories
RUN mkdir -p /app/data /app/experiments

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
