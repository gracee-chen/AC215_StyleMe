# Use CUDA-enabled base image for GPU support (includes Python)
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Install Python 3 and pip if not already present
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Set working directory
WORKDIR /app

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
