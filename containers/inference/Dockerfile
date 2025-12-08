FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies including gcsfuse for GCS mounting
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    libgl1 \
    libglib2.0-0 \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install gcsfuse for mounting GCS buckets (using modern apt keyring method)
RUN export GCSFUSE_REPO=gcsfuse-$(lsb_release -c -s) && \
    curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt $GCSFUSE_REPO main" | tee /etc/apt/sources.list.d/gcsfuse.list && \
    apt-get update && \
    apt-get install -y gcsfuse && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY containers/inference/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    pip cache purge && \
    rm -rf /root/.cache/pip

# Pre-download CLIP model to cache (prevents Hugging Face rate limiting at runtime)
# Set cache directory and download CLIP model during build
ENV HF_HOME=/root/.cache/huggingface
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface/transformers
RUN mkdir -p /root/.cache/huggingface && \
    python3 -c "from transformers import CLIPModel, CLIPProcessor; \
    import os; \
    print('📥 Pre-downloading CLIP model to cache...'); \
    try: \
        model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', cache_dir='/root/.cache/huggingface'); \
        processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', cache_dir='/root/.cache/huggingface'); \
        print('✅ CLIP model cached successfully'); \
    except Exception as e: \
        print(f'⚠️  CLIP pre-download warning: {e}'); \
        print('   Will attempt to download on first use');" || \
    echo "⚠️  CLIP pre-download step completed with warnings"

# Pre-download CLIP model to cache (prevents rate limiting during runtime)
# This downloads the base CLIP model that FashionCLIPModel needs
RUN python3 -c "from transformers import CLIPModel, CLIPProcessor; \
    print('Pre-downloading CLIP model...'); \
    CLIPModel.from_pretrained('openai/clip-vit-base-patch32'); \
    CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32'); \
    print('✅ CLIP model cached')" || echo "⚠️  CLIP pre-download failed, will download on first use"

# Copy source code
COPY src/ /app/src/
COPY containers/inference/*.py /app/
COPY containers/inference/entrypoint.sh /app/entrypoint.sh

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Set environment variables
ENV PYTHONPATH=/app/src:/app/src/models/train:/app
# Hugging Face cache directory (persist CLIP model cache)
ENV HF_HOME=/root/.cache/huggingface
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface/transformers
ENV HF_HUB_DISABLE_TELEMETRY=1
# Default to GCS paths for Cloud Run, but can be overridden
ENV EXPERIMENTS_DIR=/gcs/styleme-production/experiments
ENV CATALOG_DIR=/gcs/styleme-production/catalog
ENV WARDROBES_DIR=/gcs/styleme-production/wardrobes
ENV QUERIES_DIR=/tmp/queries
ENV RESULTS_DIR=/tmp/results
ENV LOGS_DIR=/tmp/logs
ENV GCS_BUCKET=styleme-production

# Create directories (local temp dirs for queries/results)
RUN mkdir -p /tmp/queries /tmp/results /tmp/logs/inference /app/uploads /gcs

# Set environment variables for API
ENV PORT=5000
ENV FLASK_DEBUG=False
ENV UPLOAD_FOLDER=/app/uploads

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

