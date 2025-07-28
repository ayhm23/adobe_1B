# Adobe 1B Challenge - Model Execution Guide

## Overview
This guide explains how to run the Adobe 1B Challenge solution, with special attention to model download requirements and network usage.

## 🌐 Network Requirements

### First Run - Internet Required
**⚠️ IMPORTANT**: The first time you build the Docker image, you MUST have internet access to download the AI models.

```bash
# First build - requires internet connection
docker build -t adobe1b-solution .
```

**What happens during first build:**
- Downloads `intfloat/e5-small-v2` model (~133MB)
- Caches model in Docker image at `/app/models/sentence-transformers/`
- Sets up offline mode for future runs

### Subsequent Runs - Offline Capable
After the initial build, the container can run completely offline:

```bash
# Subsequent runs - can work offline
docker run --network none -it \
  -v "$(pwd):/app" \
  -v "$(pwd)/docker_output:/app/output" \
  adobe1b-solution
```

## 🚀 Quick Start Guide

### Step 1: Initial Setup (Internet Required)
```bash
# Clone or navigate to project directory
cd /path/to/Adobe1B

# Build Docker image (downloads models)
docker build -t adobe1b-solution .
```

### Step 2: Run with Collections (Can be Offline)
```bash
# Option A: Full workspace mount (recommended)
docker run -it \
  -v "$(pwd):/app" \
  -v "$(pwd)/docker_output:/app/output" \
  adobe1b-solution

# Option B: Offline mode (after initial build)
docker run --network none -it \
  -v "$(pwd):/app" \
  -v "$(pwd)/docker_output:/app/output" \
  adobe1b-solution
```

### Step 3: Select Collection
When the container starts, you'll see:
```
==================================================
ROUND 1B CHALLENGE - COLLECTION SELECTOR
==================================================

Available collections:
1. Collection 1 - Travel Planner
2. Collection 2 - HR Professional  
3. Collection 3 - Food Contractor

Select collection (1-3) or 'all' for all collections: 
```

## 📁 Collection Details

### Collection 1: Travel Planning
- **Persona**: Travel Planner
- **Task**: Plan a 4-day trip for 10 college friends
- **PDFs**: 7 documents about South of France

### Collection 2: HR Forms
- **Persona**: HR Professional
- **Task**: Create fillable forms for onboarding
- **PDFs**: 15 Adobe Acrobat tutorial documents

### Collection 3: Food Catering
- **Persona**: Food Contractor
- **Task**: Vegetarian buffet menu with gluten-free options
- **PDFs**: 9 documents with breakfast, lunch, and dinner ideas

## 🔧 Advanced Usage

### Force Model Re-download
If you need to refresh the models:
```bash
# Force fresh model download
docker build --build-arg CACHE_BUST=$(date +%s) -t adobe1b-solution .
```

### Windows Users
```powershell
# PowerShell equivalent
docker run -it -v "${PWD}:/app" -v "${PWD}/docker_output:/app/output" adobe1b-solution

# Offline mode
docker run --network none -it -v "${PWD}:/app" -v "${PWD}/docker_output:/app/output" adobe1b-solution
```

### Helper Scripts
Use the provided convenience scripts:
```bash
# Linux/Mac
./run_docker.sh

# Windows
run_docker.bat
```

## 📤 Output

Results are saved to:
- **Container**: `/app/output/challenge1b_output.json`
- **Host**: `./docker_output/challenge1b_output.json`

### Sample Output Structure
```json
{
  "metadata": {
    "input_documents": ["doc1.pdf", "doc2.pdf"],
    "persona": "Travel Planner",
    "job_to_be_done": "Plan a trip...",
    "processing_timestamp": "2025-07-28T15:45:14.437449"
  },
  "extracted_sections": [
    {
      "document": "Cities.pdf",
      "section_title": "Best Destinations",
      "importance_rank": 1,
      "page_number": 3
    }
  ],
  "subsection_analysis": [...]
}
```

## 🛠️ Troubleshooting

### Model Download Issues
```bash
# Error: Failed to resolve 'huggingface.co'
# Solution: Ensure internet connection during first build

# Error: Model not found in cache
# Solution: Rebuild image with fresh models
docker build --no-cache -t adobe1b-solution .
```

### PDF Not Found
```bash
# Error: No PDF files found
# Solution: Mount the correct directory
docker run -it -v "$(pwd):/app" adobe1b-solution
```

### Offline Mode Issues
```bash
# Error: Network required
# Solution: Build image first with internet, then use --network none
docker build -t adobe1b-solution .  # With internet
docker run --network none ...        # Offline mode
```

## 📊 Performance Notes

### Build Time
- **First build**: ~5-10 minutes (downloading models)
- **Subsequent builds**: ~1-2 minutes (cached layers)

### Runtime
- **Model loading**: ~5-10 seconds (from cache)
- **PDF processing**: ~30 seconds per collection
- **Total per collection**: ~1-2 minutes

### Resource Usage
- **Memory**: ~2-4 GB RAM recommended
- **Storage**: ~2 GB for Docker image
- **Network**: ~200MB for initial model download

## 🔒 Security Considerations

### Offline Operation
After initial build, the container can run completely offline:
- No external network calls during processing
- Models cached locally in container
- Safe for air-gapped environments

### Data Privacy
- PDFs processed locally only
- No data sent to external services
- All processing happens within container

## 📋 Model Information

### Sentence Transformers Model
- **Model**: `intfloat/e5-small-v2`
- **Size**: ~133MB
- **Purpose**: Semantic similarity matching
- **Cache Location**: `/app/models/sentence-transformers/`

### PaddleOCR (Optional)
- **Status**: Disabled by default
- **Size**: ~500MB if enabled
- **Purpose**: Advanced layout detection
- **Note**: System works well without it

## 🚀 Production Deployment

### Air-Gapped Environments
1. Build image on internet-connected machine
2. Export image: `docker save adobe1b-solution > adobe1b.tar`
3. Transfer to air-gapped system
4. Import image: `docker load < adobe1b.tar`
5. Run with `--network none`

### CI/CD Pipeline
```yaml
# Example GitHub Actions
- name: Build Docker Image
  run: docker build -t adobe1b-solution .
  
- name: Test Offline Mode
  run: docker run --network none adobe1b-solution --help
```

## 📞 Support

For issues or questions:
1. Check this documentation
2. Review error messages
3. Ensure proper volume mounts
4. Verify internet connection for first build
5. Try rebuilding with `--no-cache` if needed
