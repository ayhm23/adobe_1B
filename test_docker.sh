#!/bin/bash

# Build the Docker image
echo "Building Docker image..."
docker build -t adobe1b-solution .

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
    echo ""
    echo "To run the container with your data:"
    echo "1. Create a 'data' folder with Collection_1, Collection_2, Collection_3 subfolders"
    echo "2. Run: docker run -it -v \$(pwd)/data:/app/data -v \$(pwd)/docker_output:/app/output adobe1b-solution"
    echo ""
    echo "The container will:"
    echo "- Download PP-DocLayout-M model to /app/models"
    echo "- Show available collections"
    echo "- Process selected collection with Round 1B format"
    echo "- Save results to /app/output (mapped to ./docker_output on host)"
else
    echo "❌ Docker build failed!"
    exit 1
fi
