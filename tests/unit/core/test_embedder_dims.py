"""Test embedder dimensions to ensure proper 384-d and 768-d outputs."""

import pytest
import numpy as np
from pathlib import Path
import os
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.her.embeddings.text_embedder import TextEmbedder
from src.her.embeddings.markuplm_embedder import MarkupLMEmbedder
from src.her.embeddings.element_embedder import ElementEmbedder


class TestEmbedderDimensions:
    """Test that embedders output correct dimensions."""
    
    def test_text_embedder_384d(self):
        """Test that TextEmbedder outputs 384-dimensional vectors."""
        # Skip if models not available
        model_path = Path("src/her/models/e5-small-onnx")
        if not model_path.exists():
            pytest.skip("MiniLM model not found - run install_models.sh first")
        
        embedder = TextEmbedder(model_root=str(model_path))
        
        # Test single text
        text = "click on phones button"
        vec = embedder.encode_one(text)
        
        assert vec.shape == (384,), f"Expected 384-d, got {vec.shape}"
        assert vec.dtype == np.float32, f"Expected float32, got {vec.dtype}"
        
        # Test batch
        texts = ["click phones", "select apple", "open menu"]
        batch_vecs = embedder.batch_encode_texts(texts)
        
        assert batch_vecs.shape == (3, 384), f"Expected (3, 384), got {batch_vecs.shape}"
        assert batch_vecs.dtype == np.float32, f"Expected float32, got {batch_vecs.dtype}"
        
        # Test normalization
        norms = np.linalg.norm(batch_vecs, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-6), "Vectors should be normalized"
    
    def test_markuplm_embedder_768d(self):
        """Test that MarkupLMEmbedder outputs 768-dimensional vectors."""
        # Skip if models not available
        model_path = Path("src/her/models/markuplm-base")
        if not model_path.exists():
            pytest.skip("MarkupLM model not found - run install_models.sh first")
        
        embedder = MarkupLMEmbedder(model_dir=str(model_path))
        
        # Test single element
        element = {
            "text": "click on phones button",
            "tag": "button",
            "attributes": {"class": "btn-primary"}
        }
        vec = embedder.encode(element)
        
        assert vec.shape == (768,), f"Expected 768-d, got {vec.shape}"
        assert vec.dtype == np.float32, f"Expected float32, got {vec.dtype}"
        
        # Test batch
        elements = [
            {"text": "click phones", "tag": "a", "attributes": {"href": "/phones"}},
            {"text": "select apple", "tag": "button", "attributes": {"class": "filter"}},
            {"text": "open menu", "tag": "div", "attributes": {"role": "button"}}
        ]
        batch_vecs = embedder.batch_encode(elements)
        
        assert batch_vecs.shape == (3, 768), f"Expected (3, 768), got {batch_vecs.shape}"
        assert batch_vecs.dtype == np.float32, f"Expected float32, got {batch_vecs.dtype}"
        
        # Test normalization
        norms = np.linalg.norm(batch_vecs, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-6), "Vectors should be normalized"
    
    def test_element_embedder_768d(self):
        """Test that ElementEmbedder outputs 768-dimensional vectors."""
        embedder = ElementEmbedder(dim=768)
        
        # Test single element
        element = {
            "text": "click on phones button",
            "tag": "button",
            "attributes": {"class": "btn-primary"}
        }
        vec = embedder.encode(element)
        
        assert vec.shape == (768,), f"Expected 768-d, got {vec.shape}"
        assert vec.dtype == np.float32, f"Expected float32, got {vec.dtype}"
        
        # Test batch
        elements = [
            {"text": "click phones", "tag": "a", "attributes": {"href": "/phones"}},
            {"text": "select apple", "tag": "button", "attributes": {"class": "filter"}},
            {"text": "open menu", "tag": "div", "attributes": {"role": "button"}}
        ]
        batch_vecs = embedder.batch_encode(elements)
        
        assert batch_vecs.shape == (3, 768), f"Expected (3, 768), got {batch_vecs.shape}"
        assert batch_vecs.dtype == np.float32, f"Expected float32, got {batch_vecs.dtype}"
        
        # Test normalization
        norms = np.linalg.norm(batch_vecs, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-6), "Vectors should be normalized"
    
    def test_dimension_consistency(self):
        """Test that all embedders maintain consistent dimensions."""
        # Test that TextEmbedder is 384-d
        model_path = Path("src/her/models/e5-small-onnx")
        if model_path.exists():
            text_emb = TextEmbedder(model_root=str(model_path))
            assert text_emb.dim == 384, f"TextEmbedder should be 384-d, got {text_emb.dim}"
        
        # Test that MarkupLMEmbedder is 768-d
        markup_path = Path("src/her/models/markuplm-base")
        if markup_path.exists():
            markup_emb = MarkupLMEmbedder(model_dir=str(markup_path))
            assert markup_emb.dim == 768, f"MarkupLMEmbedder should be 768-d, got {markup_emb.dim}"
        
        # Test that ElementEmbedder is 768-d
        elem_emb = ElementEmbedder(dim=768)
        assert elem_emb.dim == 768, f"ElementEmbedder should be 768-d, got {elem_emb.dim}"
    
    def test_empty_inputs(self):
        """Test that embedders handle empty inputs gracefully."""
        # Test TextEmbedder with empty input
        model_path = Path("src/her/models/e5-small-onnx")
        if model_path.exists():
            text_emb = TextEmbedder(model_root=str(model_path))
            empty_vecs = text_emb.batch_encode_texts([])
            assert empty_vecs.shape == (0, 384), f"Expected (0, 384), got {empty_vecs.shape}"
        
        # Test MarkupLMEmbedder with empty input
        markup_path = Path("src/her/models/markuplm-base")
        if markup_path.exists():
            markup_emb = MarkupLMEmbedder(model_dir=str(markup_path))
            empty_vecs = markup_emb.batch_encode([])
            assert empty_vecs.shape == (0, 768), f"Expected (0, 768), got {empty_vecs.shape}"
        
        # Test ElementEmbedder with empty input
        elem_emb = ElementEmbedder(dim=768)
        empty_vecs = elem_emb.batch_encode([])
        assert empty_vecs.shape == (0, 768), f"Expected (0, 768), got {empty_vecs.shape}"