# Dockerfile for Round 1B Challenge - Linux/AMD64
FROM --platform=linux/amd64 python:3.10-slim

# Build argument to force model re-download when needed

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    tar \
    unzip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libgtk-3-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install PyTorch CPU-only first
RUN pip install --no-cache-dir torch==2.3.1+cpu torchvision==0.18.1+cpu torchaudio==2.3.1+cpu --index-url https://download.pytorch.org/whl/cpu

# Install other Python dependencies
RUN pip install --no-cache-dir -r requirements.txt


ARG CACHE_BUST=1

# Copy application code
COPY src/ src/
COPY config.json .
COPY config_docker.json .
COPY select_collection.py .
COPY extract1btent.py .
COPY download_models.py .

# Copy setup script and startup script, make them executable
COPY setup_models.sh .
COPY startup.sh .

ARG CACHE_BUST=1

RUN chmod +x setup_models.sh startup.sh

# Set environment variables for model downloads
ENV PYTHONPATH=/app
ENV CUDA_VISIBLE_DEVICES=""
ENV SENTENCE_TRANSFORMERS_HOME=/app/models/sentence-transformers
ENV HF_HOME=/app/models/huggingface

# Create necessary directories and download models in one step to avoid caching issues
# Use CACHE_BUST argument to force re-download when needed
RUN echo "Cache bust: $CACHE_BUST" && \
    mkdir -p /app/models /app/output /app/data && \
    python3 download_models.py

# Set offline mode after download
# ENV HF_HUB_OFFLINE=1

# Expose port (if needed for web interface later)
EXPOSE 8080

# Set the startup command
CMD ["/app/startup.sh"]
