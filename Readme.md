# Round 1B Challenge - Complete Solution

This solution provides a production-ready system for extracting and formatting document intelligence according to the Round 1B challenge requirements.

## Features

- **Hybrid Heading Extraction**: Combines AI layout detection with heuristic text analysis
- **Semantic Matching**: Uses transformer models to match content to persona requirements
- **Round 1B Compliance**: Generates exact output format required by the challenge
- **Multi-Collection Support**: Process multiple document collections with different configurations
- **Configurable**: Easy configuration through JSON file

## Quick Start

### Option 1: Process All Collections
```powershell
python extract1btent_complete.py
```

### Option 2: Process Specific Collection
```powershell
python extract1btent_complete.py --collection "Collection 1"
```

### Option 3: Use Batch Script (Windows)
```powershell
run_all_collections.bat
```

## Docker Deployment

### ⚠️ Important: Network Requirements

**First Build - Internet Required**:
```bash
# MUST have internet connection for first build
docker build -t adobe1b-solution .
```

**Subsequent Runs - Offline Capable**:
```bash
# After first build, can run completely offline
docker run --network none -it \
  -v "$(pwd):/app" \
  -v "$(pwd)/docker_output:/app/output" \
  adobe1b-solution
```

### Building the Docker Image
```bash
docker build -t adobe1b-solution .
```

**Force Model Re-download** (if needed):
```bash
# Force fresh model download (bypasses Docker cache)
docker build --build-arg CACHE_BUST=$(date +%s) -t adobe1b-solution .
```

### Running with Docker

#### Option 1: Mount Entire Workspace (Recommended)
This option mounts the entire workspace, allowing the container to access all collections:

```bash
# From the project root directory
docker run -it \
  -v "$(pwd):/app" \
  -v "$(pwd)/docker_output:/app/output" \
  adobe1b-solution
```

For Windows PowerShell:
```powershell
docker run -it -v "${PWD}:/app" -v "${PWD}/docker_output:/app/output" adobe1b-solution
```

#### Option 2: Offline Mode (After Initial Build)
After the first build, you can run completely offline:

```bash
docker run --network none -it \
  -v "$(pwd):/app" \
  -v "$(pwd)/docker_output:/app/output" \
  adobe1b-solution
```

#### Option 3: Mount Specific PDF Directory
If you want to process PDFs from a different location:

```bash
docker run -it \
  -v "/path/to/your/pdfs:/app/data" \
  -v "$(pwd)/docker_output:/app/output" \
  adobe1b-solution
```

### Docker Features
- **Interactive Collection Selection**: Choose which collection to process
- **Automatic Configuration**: Uses Docker-specific paths
- **Output Persistence**: Results saved to mounted output directory
- **Multi-Collection Support**: Process any or all collections
- **Pre-downloaded Models**: All AI models are downloaded during build time for faster startup
- **Offline Capability**: Can run completely offline after initial build
- **Air-Gap Ready**: Perfect for secure/isolated environments
- **Optimized Performance**: No runtime model downloads, ready to process immediately

### Docker Configuration
The Docker container uses `config_docker.json` which is automatically configured for:
- Collection 1: Travel planning documents
- Collection 2: HR forms and onboarding
- Collection 3: Food/catering menu planning

Each collection includes the appropriate persona and job requirements.

## Configuration

Edit `config.json` to customize:

```json
{
  "collections": {
    "Collection 1": {
      "input_folder": "path/to/pdfs",
      "persona": "Tax Consultant",
      "job_to_be_done": "make a list of items taxed at over 5 percent",
      "job_query": "make a list of items taxed at over 5 percent"
    }
  },
  "output_settings": {
    "output_folder": "output",
    "save_individual_results": true,
    "top_k_matches": 5
  }
}
```

## Output Structure

```
output/
├── Collection 1/
│   ├── challenge1b_output.json      # Round 1B format
│   ├── document1_results.json       # Individual results
│   └── document2_results.json
├── Collection 2/
│   └── challenge1b_output.json
└── Collection 3/
    └── challenge1b_output.json
```

## Round 1B Output Format

The system generates compliant output with:

- **Metadata**: Input documents, persona, job description, timestamp
- **Extracted Sections**: Ranked sections with importance scores
- **Subsection Analysis**: Detailed content analysis per document

Example output:
```json
{
  "metadata": {
    "input_documents": ["doc1.pdf", "doc2.pdf"],
    "persona": "Tax Consultant",
    "job_to_be_done": "make a list of items taxed at over 5 percent",
    "processing_timestamp": "2025-07-28T13:30:25.628528"
  },
  "extracted_sections": [
    {
      "document": "tax_document.pdf",
      "section_title": "High Tax Rate Items",
      "importance_rank": 1,
      "page_number": 3
    }
  ],
  "subsection_analysis": [
    {
      "document": "tax_document.pdf",
      "refined_text": "Items subject to taxation exceeding 5%...",
      "page_number": 3
    }
  ]
}
```

## Advanced Usage

### Command Line Options
- `--collection`: Process specific collection
- `--config`: Use custom configuration file
- `--output`: Set custom output directory

### Custom Configuration
Create your own config file and use it:
```powershell
python extract1btent_complete.py --config my_config.json --output my_output
```

## Technical Details

### Ranking System
The system automatically ranks sections by:
1. Semantic similarity to job query
2. Cross-document importance analysis
3. Persona-driven relevance scoring

### Processing Pipeline
1. **PDF Analysis**: Extract text and formatting information
2. **Heading Detection**: AI + heuristic heading identification
3. **Semantic Matching**: Match content to persona requirements
4. **Section Extraction**: Extract relevant content sections
5. **Cross-Document Ranking**: Rank all sections across documents
6. **Format Generation**: Create Round 1B compliant output

## Dependencies

- PyMuPDF (fitz)
- sentence-transformers
- PaddleOCR (optional, for enhanced layout detection)
- Standard Python libraries

## Troubleshooting

### Common Issues

1. **No PDF files found**: Check that the input folder paths in config.json are correct
2. **Permission errors**: Ensure you have read access to PDF files and write access to output folder
3. **Memory issues**: For large document collections, process one collection at a time

### Performance Tips

- Use SSD storage for faster PDF processing
- Increase available RAM for large documents
- Enable layout detection only if needed (requires more resources)
- **Docker**: Models are pre-downloaded during build time, eliminating runtime downloads
- **Local**: First run will download models, subsequent runs will use cached models

## Integration with Original Code

Your existing `extract1btent.py` has been enhanced with:
- Round1BFormatter class integration
- Page number tracking
- Cross-document analysis
- Automated ranking system

The original functionality is preserved while adding Round 1B compliance.

## Development Notes

### File Structure
- **Source Code**: `src/` directory contains modular components
- **Models**: Pre-trained models stored in `models/` directory
- **Output**: Results saved to `output/` (local) or `docker_output/` (Docker)
- **Configuration**: Separate configs for local (`config.json`) and Docker (`config_docker.json`)

### Version Control
- **`.gitignore`**: Excludes output directories, Python cache, virtual environments, and downloaded models
- **`.dockerignore`**: Optimizes Docker builds by excluding development files, documentation, and large data files

### Docker Optimization
- Models are downloaded during build time, not runtime
- PDFs are mounted as volumes for flexibility
- Separate configurations for container and local environments
