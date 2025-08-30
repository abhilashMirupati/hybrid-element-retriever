# archived duplicate of src/her/embeddings/_resolve.py
"""Model resolution for embeddings."""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ModelResolver:
    """Resolves model paths with fallback order.
    
    Search order:
    1. HER_MODELS_DIR environment variable
    2. Packaged models in src/her/models/
    3. User home ~/.her/models/
    """
    
    def __init__(self):
        self.model_info: Optional[Dict] = None
        self.models_dir: Optional[Path] = None
        self._initialize()
        
    def _initialize(self) -> None:
        """Initialize model resolver."""
        # Try environment variable first
        if env_dir := os.environ.get('HER_MODELS_DIR'):
            env_path = Path(env_dir)
            if env_path.exists():
                self.models_dir = env_path
                logger.info(f"Using models from HER_MODELS_DIR: {env_path}")
                
        # Try packaged models
        if not self.models_dir:
            package_dir = Path(__file__).parent.parent / 'models'
            if package_dir.exists():
                self.models_dir = package_dir
                logger.info(f"Using packaged models: {package_dir}")
                
        # Try user home directory
        if not self.models_dir:
            home_dir = Path.home() / '.her' / 'models'
            if home_dir.exists():
                self.models_dir = home_dir
                logger.info(f"Using user models: {home_dir}")
            else:
                # Create if doesn't exist
                home_dir.mkdir(parents=True, exist_ok=True)
                self.models_dir = home_dir
                logger.info(f"Created user models directory: {home_dir}")
                
        # Load MODEL_INFO.json
        info_path = self.models_dir / 'MODEL_INFO.json'
        if info_path.exists():
            with open(info_path) as f:
                self.model_info = json.load(f)
                logger.info(f"Loaded MODEL_INFO.json with {len(self.model_info)} models")
        else:
            logger.warning(f"MODEL_INFO.json not found at {info_path}")
            self.model_info = {}
            
    def resolve_model(self, model_name: str) -> Tuple[Optional[Path], Optional[Dict]]:
        """Resolve model path and info.
        
        Args:
            model_name: Name of model to resolve
            
        Returns:
            Tuple of (model_path, model_info) or (None, None) if not found
        """
        if not self.model_info or model_name not in self.model_info:
            logger.error(f"Model {model_name} not found in MODEL_INFO.json")
            return None, None
            
        info = self.model_info[model_name]
        model_path = self.models_dir / info['path']
        
        if not model_path.exists():
            logger.error(f"Model file not found: {model_path}")
            return None, None
            
        return model_path, info
        
    def get_query_embedder_info(self) -> Tuple[Optional[Path], Optional[Dict]]:
        """Get query embedder model info.
        
        Returns:
            Tuple of (model_path, model_info)
        """
        # Find query embedder
        for name, info in (self.model_info or {}).items():
            if info.get('type') == 'query_embedder':
                return self.resolve_model(name)
        return None, None
        
    def get_element_embedder_info(self) -> Tuple[Optional[Path], Optional[Dict]]:
        """Get element embedder model info.
        
        Returns:
            Tuple of (model_path, model_info)
        """
        # Find element embedder
        for name, info in (self.model_info or {}).items():
            if info.get('type') == 'element_embedder':
                return self.resolve_model(name)
        return None, None
        
    def list_models(self) -> Dict[str, Dict]:
        """List all available models.
        
        Returns:
            Dictionary of model name to info
        """
        return self.model_info or {}