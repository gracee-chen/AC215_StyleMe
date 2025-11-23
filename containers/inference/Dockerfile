FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY containers/inference/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ /app/src/
COPY containers/inference/*.py /app/
COPY containers/inference/entrypoint.sh /app/entrypoint.sh

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Set environment variables
ENV PYTHONPATH=/app/src:/app/src/models/train:/app
ENV EXPERIMENTS_DIR=/app/experiments
ENV CATALOG_DIR=/app/catalog
ENV WARDROBES_DIR=/app/wardrobes
ENV QUERIES_DIR=/app/queries
ENV RESULTS_DIR=/app/results
ENV LOGS_DIR=/app/logs

# Create directories
RUN mkdir -p /app/catalog /app/wardrobes /app/queries /app/results /app/logs/inference

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

