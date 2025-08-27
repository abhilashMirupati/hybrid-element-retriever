#!/bin/bash
# Install ONNX models for HER

set -e

echo "Installing ONNX models for Hybrid Element Retriever..."

# Create models directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MODEL_DIR="$SCRIPT_DIR/../src/her/models"
mkdir -p "$MODEL_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required"
    exit 1
fi

# Create Python script to download and export models
cat > /tmp/export_models.py << 'EOF'
#!/usr/bin/env python3
"""Export Hugging Face models to ONNX format."""

import sys
import os
from pathlib import Path

def export_models(model_dir):
    """Export models to ONNX format."""
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    
    print("Checking for required packages...")
    
    # Check for required packages
    try:
        import torch
        import transformers
        import onnx
        import onnxruntime
    except ImportError as e:
        print(f"Missing required package: {e}")
        print("Installing required packages...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", 
                              "torch", "transformers", "onnx", "onnxruntime"])
        import torch
        import transformers
        import onnx
        import onnxruntime
    
    from transformers import AutoModel, AutoTokenizer
    
    # Model configurations
    models = [
        {
            "name": "minilm-e5-small",
            "model_id": "sentence-transformers/all-MiniLM-L6-v2",
            "output": model_dir / "minilm-e5-small.onnx"
        },
        {
            "name": "markuplm-base",
            "model_id": "microsoft/markuplm-base",
            "output": model_dir / "markuplm-base.onnx"
        }
    ]
    
    for config in models:
        output_path = config["output"]
        
        if output_path.exists():
            print(f"Model already exists: {output_path}")
            continue
        
        print(f"Downloading {config['name']} from {config['model_id']}...")
        
        try:
            # Load model and tokenizer
            model = AutoModel.from_pretrained(config["model_id"])
            tokenizer = AutoTokenizer.from_pretrained(config["model_id"])
            
            # Prepare dummy input
            dummy_input = tokenizer("Hello world", return_tensors="pt")
            
            # Export to ONNX
            print(f"Exporting to ONNX: {output_path}")
            torch.onnx.export(
                model,
                tuple(dummy_input.values()),
                str(output_path),
                input_names=list(dummy_input.keys()),
                output_names=["output"],
                dynamic_axes={
                    "input_ids": {0: "batch_size", 1: "sequence"},
                    "attention_mask": {0: "batch_size", 1: "sequence"},
                    "output": {0: "batch_size"}
                },
                opset_version=11,
                do_constant_folding=True
            )
            
            print(f"Successfully exported: {output_path}")
            
            # Verify the model
            print(f"Verifying ONNX model...")
            onnx_model = onnx.load(str(output_path))
            onnx.checker.check_model(onnx_model)
            
            # Test with ONNX Runtime
            session = onnxruntime.InferenceSession(str(output_path))
            print(f"Model verified successfully!")
            
        except Exception as e:
            print(f"Warning: Failed to export {config['name']}: {e}")
            print("The system will use deterministic fallback embeddings.")
            
            # Create a placeholder file to prevent re-download attempts
            output_path.touch()
    
    print("\nModel installation complete!")
    print("Note: If models failed to export, the system will use deterministic fallback embeddings.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        model_dir = sys.argv[1]
    else:
        model_dir = Path(__file__).parent.parent / "src" / "her" / "models"
    
    export_models(model_dir)
EOF

# Run the export script
echo "Exporting models to ONNX format..."
python3 /tmp/export_models.py "$MODEL_DIR"

# Clean up
rm -f /tmp/export_models.py

echo "Model installation complete!"
echo "Models are stored in: $MODEL_DIR"