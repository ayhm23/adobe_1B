#!/bin/bash

# Adobe 1B Challenge - Docker Runner Script
# This script helps you run the Docker container with the correct volume mounts

set -e

echo "=========================================="
echo "Adobe 1B Challenge - Docker Runner"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH"
    exit 1
fi

# Get the current directory
WORKSPACE_DIR=$(pwd)
echo "Workspace directory: $WORKSPACE_DIR"

# Create output directory if it doesn't exist
mkdir -p docker_output

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    echo "Error: Dockerfile not found. Please run this script from the project root directory."
    exit 1
fi

# Build the Docker image
echo ""
echo "Building Docker image..."
echo "Note: Use --build-arg CACHE_BUST=\$(date +%s) to force model re-download"
docker build -t adobe1b-solution .

# Check if Challenge_1b directory exists
if [ -d "Challenge_1b" ]; then
    echo ""
    echo "Found Challenge_1b directory with collections:"
    for collection_dir in Challenge_1b/Collection*/; do
        if [ -d "$collection_dir" ]; then
            collection_name=$(basename "$collection_dir")
            pdf_count=$(find "$collection_dir/PDFs" -name "*.pdf" 2>/dev/null | wc -l)
            echo "  - $collection_name: $pdf_count PDF files"
        fi
    done
    
    echo ""
    echo "Running Docker container with full workspace mount..."
    echo "This will allow access to all collections."
    
    docker run -it \
        -v "$WORKSPACE_DIR:/app" \
        -v "$WORKSPACE_DIR/docker_output:/app/output" \
        adobe1b-solution
        
else
    echo ""
    echo "Challenge_1b directory not found."
    echo "Please ensure you're running this from the correct directory or"
    echo "mount your PDF directory manually using:"
    echo ""
    echo "  docker run -it -v /path/to/pdfs:/app/data -v $WORKSPACE_DIR/docker_output:/app/output adobe1b-solution"
fi
