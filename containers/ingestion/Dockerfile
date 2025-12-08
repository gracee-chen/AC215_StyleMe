FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY containers/ingestion/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    pip cache purge && \
    rm -rf /root/.cache/pip

# Copy source code
COPY src/ /app/src/
COPY containers/ingestion/entrypoint.sh /app/entrypoint.sh

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Set environment variables
ENV PYTHONPATH=/app/src
ENV DATA_DIR=/app/data

# Create data directory
RUN mkdir -p /app/data

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

