#!/bin/bash
set -e

echo "=========================================="
echo "Round 1B Challenge Docker Container"
echo "=========================================="

# Setup models
echo "Setting up models..."
# /app/setup_models.sh

# Check if PDFs directory exists and has files
if [ -d "/app/data" ] && [ "$(ls -A /app/data/*.pdf 2>/dev/null)" ]; then
    echo "PDF files found in /app/data"
    ls -la /app/data/*.pdf
else
    echo "No PDF files found in /app/data"
    
    # Check if Challenge_1b collections exist (when mounting entire workspace)
    if [ -d "/app/Challenge_1b" ]; then
        echo "Found Challenge_1b collections directory"
        echo "Available collections:"
        for collection_dir in /app/Challenge_1b/Collection*/; do
            if [ -d "$collection_dir" ]; then
                collection_name=$(basename "$collection_dir")
                pdf_count=$(find "$collection_dir/PDFs" -name "*.pdf" 2>/dev/null | wc -l)
                echo "  - $collection_name: $pdf_count PDF files"
            fi
        done
        echo ""
        echo "The system will use the collections from Challenge_1b directory."
    else
        echo "Please mount your PDF directory to /app/data or mount the entire workspace"
        echo ""
        echo "Example usage options:"
        echo "  # Option 1: Mount specific PDF directory"
        echo "  docker run -v /path/to/your/pdfs:/app/data adobe1b-challenge"
        echo ""
        echo "  # Option 2: Mount entire workspace (recommended for collections)"
        echo "  docker run -v /path/to/workspace:/app adobe1b-challenge"
        echo ""
    fi
fi

# Start the collection selector
echo "Starting collection selector..."

# Check if we're in Docker (use Docker config) or local environment
if [ -f "/app/config_docker.json" ] && [ -d "/app/Challenge_1b" ]; then
    echo "Using Docker configuration..."
    export CONFIG_PATH="/app/config_docker.json"
    python3 select_collection.py
elif [ -f "/app/config.json" ]; then
    echo "Using local configuration..."
    python3 select_collection.py
else
    echo "Error: No configuration file found!"
    exit 1
fi
