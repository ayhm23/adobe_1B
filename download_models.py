#!/usr/bin/env python3
"""
Pre-download and initialize models during Docker build
This prevents runtime downloads and improves container startup time
"""

import os
from sentence_transformers import SentenceTransformer

def download_sentence_transformers():
    """Download sentence-transformers model to cache directory"""
    print("=== Downloading sentence-transformers model ===")
    
    # Set cache directory to models folder
    cache_dir = "/app/models/sentence-transformers"
    os.makedirs(cache_dir, exist_ok=True)
    
    # Set environment variables for sentence-transformers cache
    os.environ['SENTENCE_TRANSFORMERS_HOME'] = cache_dir
    os.environ['HF_HOME'] = "/app/models/huggingface"
    
    # Download the model
    model_name = "intfloat/e5-small-v2"
    print(f"Downloading {model_name} to {cache_dir}...")
    
    try:
        # Download with explicit cache folder
        model = SentenceTransformer(model_name, cache_folder=cache_dir)
        print(f"✓ Successfully downloaded {model_name}")
        
        # Verify the model cache structure
        model_cache_path = os.path.join(cache_dir, f"models--{model_name.replace('/', '--')}")
        if os.path.exists(model_cache_path):
            print(f"✓ Model cached at: {model_cache_path}")
        else:
            print(f"⚠ Model cache structure may be different")
            
        # Test the model to ensure it's working
        test_text = "This is a test sentence."
        embedding = model.encode(test_text)
        print(f"✓ Model test successful. Embedding shape: {embedding.shape}")
        
        # Set offline mode for future use
        os.environ['HF_HUB_OFFLINE'] = '1'
        print("✓ Offline mode enabled for future model loading")
        
    except Exception as e:
        print(f"✗ Error downloading sentence-transformers model: {e}")
        raise

def initialize_paddleocr():
    """Initialize PaddleOCR to download any missing components"""
    print("\n=== Initializing PaddleOCR ===")
    
    try:
        from paddleocr import LayoutDetection
        print("PaddleOCR is available")
        
        # Check if PP-DocLayout models exist
        model_dirs = [
            "/app/models/PP-DocLayout-M"   
        ]
        
        for model_dir in model_dirs:
            if os.path.exists(model_dir):
                print(f"✓ Found {os.path.basename(model_dir)} model")
            else:
                print(f"✗ Missing {os.path.basename(model_dir)} model")
        
        # Initialize layout detection to trigger any additional downloads
        print("Initializing layout detection...")
        layout_model = LayoutDetection(
            model_dir="/app/models/PP-DocLayout-M",
            device="cpu"
        )
        print("✓ PaddleOCR layout detection initialized successfully")
        
    except ImportError:
        print("PaddleOCR not available - this is optional")
    except Exception as e:
        print(f"Warning: PaddleOCR initialization failed: {e}")
        print("This is not critical - the system will work without layout detection")

def download_models():
    """Download and initialize all required models"""
    print("========================================")
    print("Pre-downloading models for Adobe 1B Challenge")
    print("========================================")
    
    download_sentence_transformers()
    #initialize_paddleocr()
    
    print("\n========================================")
    print("All models downloaded and initialized successfully!")
    print("========================================")

if __name__ == "__main__":
    download_models()
