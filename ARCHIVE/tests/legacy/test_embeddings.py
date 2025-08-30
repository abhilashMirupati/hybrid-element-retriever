"""Tests for embedding modules."""

import pytest
import numpy as np
# from pathlib import Path
import tempfile

from her.embeddings._resolve import (
    ONNXModelResolver,
    get_query_resolver,
    get_element_resolver,
)
from her.embeddings.query_embedder import QueryEmbedder
from her.embeddings.element_embedder import ElementEmbedder
from her.embeddings.cache import EmbeddingCache


class TestONNXResolver:
    """Test ONNX model resolver."""

    def test_init_without_model(self):
        """Test initialization without model file."""
        resolver = ONNXModelResolver()
        assert resolver.model_path is None
        assert resolver.session is None

    def test_init_with_missing_model(self):
        """Test initialization with missing model file."""
        resolver = ONNXModelResolver("/nonexistent/model.onnx")
        assert resolver.session is None

    def test_deterministic_embedding(self):
        """Test deterministic embedding generation."""
        resolver = ONNXModelResolver()

        # Same text should produce same embedding
        text = "test query"
        emb1 = resolver.embed(text)
        emb2 = resolver.embed(text)

        assert isinstance(emb1, np.ndarray)
        assert emb1.shape == (384,)  # Default dimension
        assert np.allclose(emb1, emb2)
        assert np.abs(np.linalg.norm(emb1) - 1.0) < 0.01  # Unit vector

    def test_different_texts_different_embeddings(self):
        """Test that different texts produce different embeddings."""
        resolver = ONNXModelResolver()

        emb1 = resolver.embed("query one")
        emb2 = resolver.embed("query two")

        assert not np.allclose(emb1, emb2)


class TestQueryEmbedder:
    """Test query embedder."""

    def test_init(self):
        """Test initialization."""
        embedder = QueryEmbedder()
        assert embedder.cache is not None
        assert embedder.resolver is not None
        assert embedder.dim == 384

    def test_embed(self):
        """Test embedding generation."""
        embedder = QueryEmbedder()

        embedding = embedder.embed("login button")
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)

    def test_cache_hit(self):
        """Test cache functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = EmbeddingCache(db_path=Path(tmpdir) / "cache.db")
            embedder = QueryEmbedder(cache=cache)

            # First call - cache miss
            emb1 = embedder.embed("test query")

            # Second call - should be cache hit
            emb2 = embedder.embed("test query")

            assert np.allclose(emb1, emb2)
            assert cache._hits > 0

    def test_embed_batch(self):
        """Test batch embedding."""
        embedder = QueryEmbedder()

        texts = ["button", "input field", "dropdown menu"]
        embeddings = embedder.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(isinstance(e, np.ndarray) for e in embeddings)
        assert all(e.shape == (384,) for e in embeddings)

    def test_similarity(self):
        """Test similarity computation."""
        embedder = QueryEmbedder()

        vec1 = np.array([1, 0, 0])
        vec2 = np.array([1, 0, 0])
        vec3 = np.array([0, 1, 0])

        assert embedder.similarity(vec1, vec2) > 0.99
        assert embedder.similarity(vec1, vec3) < 0.01


class TestElementEmbedder:
    """Test element embedder."""

    def test_init(self):
        """Test initialization."""
        embedder = ElementEmbedder()
        assert embedder.cache is not None
        assert embedder.resolver is not None

    def test_embed_element(self):
        """Test element embedding."""
        embedder = ElementEmbedder()

        element = {
            "tag": "button",
            "text": "Submit",
            "role": "button",
            "name": "submit-btn",
            "id": "submit",
            "classes": ["btn", "btn-primary"],
        }

        embedding = embedder.embed(element)
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)

    def test_embed_batch(self):
        """Test batch element embedding."""
        embedder = ElementEmbedder()

        elements = [
            {"tag": "button", "text": "Click me"},
            {"tag": "input", "placeholder": "Enter text"},
            {"tag": "select", "name": "dropdown"},
        ]

        embeddings = embedder.embed_batch(elements)
        assert len(embeddings) == 3
        assert all(isinstance(e, np.ndarray) for e in embeddings)

    def test_element_to_text(self):
        """Test element to text conversion."""
        embedder = ElementEmbedder()

        element = {
            "tag": "input",
            "type": "email",
            "placeholder": "Enter email",
            "id": "email-input",
            "classes": ["form-control"],
            "aria": {"label": "Email address"},
        }

        text = embedder._element_to_text(element)
        assert "tag:input" in text
        assert "type:email" in text
        assert "placeholder:Enter email" in text
        assert "id:email-input" in text
        assert "aria-label:Email address" in text


class TestEmbeddingCache:
    """Test embedding cache."""

    def test_init(self):
        """Test cache initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = EmbeddingCache(db_path=Path(tmpdir) / "test.db")
            assert cache.capacity == 1024
            assert len(cache._mem) == 0

    def test_put_and_get(self):
        """Test storing and retrieving embeddings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = EmbeddingCache(db_path=Path(tmpdir) / "test.db")

            vec = np.random.randn(10).astype(np.float32)
            cache.put("test_key", vec)

            retrieved = cache.get("test_key")
            assert retrieved is not None
            assert np.allclose(vec, retrieved)

    def test_lru_eviction(self):
        """Test LRU eviction."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = EmbeddingCache(capacity=2, db_path=Path(tmpdir) / "test.db")

            vec1 = np.array([1.0])
            vec2 = np.array([2.0])
            vec3 = np.array([3.0])

            cache.put("key1", vec1)
            cache.put("key2", vec2)
            cache.put("key3", vec3)  # Should evict key1

            assert len(cache._mem) == 2
            assert "key1" not in cache._mem
            assert "key2" in cache._mem
            assert "key3" in cache._mem

    def test_persistence(self):
        """Test persistence to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Store in first cache instance
            cache1 = EmbeddingCache(db_path=db_path)
            vec = np.random.randn(10).astype(np.float32)
            cache1.put("persistent_key", vec)

            # Load in second cache instance
            cache2 = EmbeddingCache(db_path=db_path)
            retrieved = cache2.get("persistent_key")

            assert retrieved is not None
            assert np.allclose(vec, retrieved)

    def test_stats(self):
        """Test cache statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = EmbeddingCache(db_path=Path(tmpdir) / "test.db")

            cache.put("key1", np.array([1.0]))
            cache.get("key1")  # Hit
            cache.get("key2")  # Miss

            stats = cache.stats()
            assert stats["hits"] == 1
            assert stats["misses"] == 1
            assert stats["memory_size"] == 1
