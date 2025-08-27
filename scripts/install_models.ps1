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
import json
from pathlib import Path
from datetime import datetime

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
                              "torch", "transformers", "onnx", "onnxruntime",
                              "sentencepiece", "protobuf"])
        import torch
        import transformers
        import onnx
        import onnxruntime
    
    from transformers import AutoModel, AutoTokenizer
    
    # Model configurations
    models = [
        {
            "name": "e5-small",
            "model_id": "intfloat/e5-small",
            "task": "query_embedding",
            "output": model_dir / "e5-small.onnx",
            "tokenizer_output": model_dir / "e5-small-tokenizer",
            "embedding_dim": 384
        },
        {
            "name": "markuplm-base", 
            "model_id": "microsoft/markuplm-base",
            "task": "element_embedding",
            "output": model_dir / "markuplm-base.onnx",
            "tokenizer_output": model_dir / "markuplm-base-tokenizer",
            "embedding_dim": 768
        }
    ]
    
    model_info = {
        "created": datetime.utcnow().isoformat(),
        "models": {}
    }
    
    for config in models:
        output_path = config["output"]
        tokenizer_path = config["tokenizer_output"]
        
        print(f"\nProcessing {config['name']}...")
        
        # Record model info
        model_info["models"][config["name"]] = {
            "huggingface_id": config["model_id"],
            "task": config["task"],
            "onnx_path": output_path.name,
            "tokenizer_path": tokenizer_path.name,
            "embedding_dim": config["embedding_dim"],
            "exported": False,
            "error": None
        }
        
        if output_path.exists() and tokenizer_path.exists():
            print(f"Model already exists: {output_path}")
            model_info["models"][config["name"]]["exported"] = True
            continue
        
        print(f"Downloading {config['name']} from {config['model_id']}...")
        
        try:
            # Load model and tokenizer
            model = AutoModel.from_pretrained(config["model_id"])
            tokenizer = AutoTokenizer.from_pretrained(config["model_id"])
            
            # Save tokenizer
            print(f"Saving tokenizer to: {tokenizer_path}")
            tokenizer.save_pretrained(str(tokenizer_path))
            
            # Prepare dummy input
            dummy_text = "This is a sample text for model export"
            dummy_input = tokenizer(dummy_text, return_tensors="pt",
                                   padding=True, truncation=True, max_length=512)
            
            # Set model to eval mode
            model.eval()
            
            # Export to ONNX
            print(f"Exporting to ONNX: {output_path}")
            
            # Get the model output for dynamic axes
            with torch.no_grad():
                model_output = model(**dummy_input)
            
            # Determine output names based on model output
            if hasattr(model_output, "last_hidden_state"):
                output_names = ["last_hidden_state"]
            elif hasattr(model_output, "pooler_output"):
                output_names = ["pooler_output"]
            else:
                output_names = ["output"]
            
            torch.onnx.export(
                model,
                tuple(dummy_input.values()),
                str(output_path),
                input_names=list(dummy_input.keys()),
                output_names=output_names,
                dynamic_axes={
                    "input_ids": {0: "batch_size", 1: "sequence"},
                    "attention_mask": {0: "batch_size", 1: "sequence"},
                    output_names[0]: {0: "batch_size"}
                },
                opset_version=11,
                do_constant_folding=True,
                export_params=True
            )
            
            print(f"Successfully exported: {output_path}")
            
            # Verify the model
            print(f"Verifying ONNX model...")
            onnx_model = onnx.load(str(output_path))
            onnx.checker.check_model(onnx_model)
            
            # Test with ONNX Runtime
            session = onnxruntime.InferenceSession(str(output_path))
            
            # Prepare inputs for ONNX runtime
            ort_inputs = {
                k: v.numpy() for k, v in dummy_input.items()
                if k in [inp.name for inp in session.get_inputs()]
            }
            
            # Run inference
            ort_outputs = session.run(None, ort_inputs)
            print(f"Model verified successfully! Output shape: {ort_outputs[0].shape}")
            
            model_info["models"][config["name"]]["exported"] = True
            
        except Exception as e:
            error_msg = str(e)
            print(f"Warning: Failed to export {config['name']}: {error_msg}")
            print("The system will use deterministic fallback embeddings.")
            
            model_info["models"][config["name"]]["exported"] = False
            model_info["models"][config["name"]]["error"] = error_msg
            
            # Create placeholder files to prevent re-download attempts
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.touch()
            tokenizer_path.mkdir(parents=True, exist_ok=True)
            (tokenizer_path / "tokenizer_config.json").write_text("{}")
    
    # Write MODEL_INFO.json
    model_info_path = model_dir / "MODEL_INFO.json"
    print(f"\nWriting model info to: {model_info_path}")
    with open(model_info_path, 'w') as f:
        json.dump(model_info, f, indent=2)
    
    print("\nModel installation complete!")
    print("Note: If models failed to export, the system will use deterministic fallback embeddings.")
    
    # Print summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    for name, info in model_info["models"].items():
        status = "✓ Exported" if info["exported"] else "✗ Fallback"
        print(f"{name}: {status}")
        if not info["exported"] and info["error"]:
            print(f"  Error: {info['error'][:100]}...")

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