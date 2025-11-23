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

# Install PyTorch with CUDA 11.8 support (compatible with CUDA 11.4 runtime)
RUN pip install --no-cache-dir torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118

# Install other dependencies (skip torch packages)
RUN pip install --no-cache-dir $(grep -v '^torch' /app/requirements.txt)

# Copy source code
COPY src/ /app/src/
COPY containers/training/entrypoint.sh /app/entrypoint.sh

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Set environment variables
ENV PYTHONPATH=/app/src
ENV EXPERIMENTS_DIR=/app/experiments
ENV CUDA_VISIBLE_DEVICES=0

# Create directories
RUN mkdir -p /app/experiments

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
