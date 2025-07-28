#!/bin/bash

# setup_models.sh - Download and setup models for Docker container

set -e

echo "Setting up models for Round 1B Challenge..."

# Create models directory
mkdir -p /app/models

# Download PP-DocLayout-M model if not exists
if [ ! -d "/app/models/PP-DocLayout-M" ]; then
    echo "Downloading PP-DocLayout-M model..."
    mkdir -p /app/models/PP-DocLayout-M
    
    # Download model files from PaddleOCR official repository
    cd /app/models/PP-DocLayout-M
    
    # Download the inference model files
    wget -q https://paddleocr.bj.bcebos.com/dygraph_v2.1/layout_analysis/PP-DocLayout-M/inference.tar
    tar -xf inference.tar
    mv inference/* .
    rm -rf inference inference.tar
    
    # Create config files
    cat > config.json << 'EOF'
{
    "Global": {
        "use_gpu": false,
        "epoch_num": 500,
        "log_smooth_window": 20,
        "print_batch_step": 10,
        "save_model_dir": "./output/",
        "save_epoch_step": 3,
        "eval_batch_step": [0, 400],
        "cal_metric_during_train": false,
        "pretrained_model": null,
        "checkpoints": null,
        "save_inference_dir": null,
        "use_visualdl": false,
        "infer_img": "doc/imgs_en/img_10.jpg",
        "save_res_path": "./output/det_db/predicts_db.txt"
    },
    "Architecture": {
        "model_type": "det",
        "algorithm": "DB",
        "Transform": null,
        "Backbone": {
            "name": "MobileNetV3",
            "scale": 0.5,
            "model_name": "large",
            "disable_se": true
        },
        "Neck": {
            "name": "DBFPN",
            "out_channels": 256
        },
        "Head": {
            "name": "DBHead",
            "k": 50
        }
    }
}
EOF

    cat > inference.yml << 'EOF'
Global:
  use_gpu: false
  epoch_num: 500
  log_smooth_window: 20
  print_batch_step: 10
  save_model_dir: ./output/
  save_epoch_step: 3
  eval_batch_step: [0, 400]
  cal_metric_during_train: False
  pretrained_model: null
  checkpoints: null
  save_inference_dir: null
  use_visualdl: False
  infer_img: doc/imgs_en/img_10.jpg
  save_res_path: ./output/det_db/predicts_db.txt
Architecture:
  model_type: det
  algorithm: DB
  Transform: null
  Backbone:
    name: MobileNetV3
    scale: 0.5
    model_name: large
    disable_se: True
  Neck:
    name: DBFPN
    out_channels: 256
  Head:
    name: DBHead
    k: 50
EOF

    echo "✓ PP-DocLayout-M model downloaded and configured"
else
    echo "✓ PP-DocLayout-M model already exists"
fi

# Update the heading extractor to use the correct model path
echo "Updating model paths for Docker environment..."

# Create a simple script to download sentence transformer model
python3 -c "
from sentence_transformers import SentenceTransformer
print('Downloading sentence transformer model...')
model = SentenceTransformer('intfloat/e5-small-v2')
print('✓ Sentence transformer model ready')
"

echo "✓ All models setup complete!"
