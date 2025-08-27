# Install ONNX models for HER (Windows PowerShell version)

$ErrorActionPreference = "Stop"

Write-Host "Installing ONNX models for Hybrid Element Retriever..." -ForegroundColor Green

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ModelDir = Join-Path $ScriptDir "..\src\her\models"

# Create models directory
New-Item -ItemType Directory -Force -Path $ModelDir | Out-Null

# Check if Python is available
try {
    python --version | Out-Null
} catch {
    Write-Host "Error: Python 3 is required" -ForegroundColor Red
    exit 1
}

# Create Python script to download and export models
$ExportScript = @'
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
    
    print("")
    print("Model installation complete!")
    print("Note: If models failed to export, the system will use deterministic fallback embeddings.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        model_dir = sys.argv[1]
    else:
        model_dir = Path(__file__).parent.parent / "src" / "her" / "models"
    
    export_models(model_dir)
'@

# Save script to temp file
$TempScript = Join-Path $env:TEMP "export_models.py"
$ExportScript | Out-File -FilePath $TempScript -Encoding UTF8

# Run the export script
Write-Host "Exporting models to ONNX format..." -ForegroundColor Yellow
python $TempScript $ModelDir

# Clean up
Remove-Item $TempScript -Force

Write-Host "Model installation complete!" -ForegroundColor Green
Write-Host "Models are stored in: $ModelDir" -ForegroundColor Cyan