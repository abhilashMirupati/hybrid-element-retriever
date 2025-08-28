"""Tests to improve resolver coverage."""

from unittest.mock import Mock, patch, MagicMock
import numpy as np
import pytest

from her.embeddings._resolve import (
    ONNXModelResolver,
    get_query_resolver,
    get_element_resolver,
)


class TestResolverCoverage:
    """Test resolver functions for coverage."""

    def test_onnx_resolver_init(self):
        """Test ONNX resolver initialization."""
        resolver = ONNXModelResolver("test-model")
        assert resolver.model_name == "test-model"
        assert resolver.embedding_dim > 0

    def test_onnx_resolver_embed_fallback(self):
        """Test fallback embedding generation."""
        resolver = ONNXModelResolver("nonexistent-model")

        # Should use deterministic fallback
        embedding = resolver.embed("test text")
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape[0] > 0

        # Same text should give same embedding
        embedding2 = resolver.embed("test text")
        np.testing.assert_array_equal(embedding, embedding2)

        # Different text should give different embedding
        embedding3 = resolver.embed("different text")
        assert not np.array_equal(embedding, embedding3)

    @patch("her.embeddings._resolve.Path")
    def test_resolver_find_model_paths(self, mock_path):
        """Test model path finding."""
        resolver = ONNXModelResolver("test-model")

        # Mock path exists
        mock_model_path = Mock()
        mock_model_path.exists.return_value = True
        mock_tokenizer_path = Mock()
        mock_tokenizer_path.exists.return_value = True

        with patch.object(resolver, "model_path", mock_model_path):
            with patch.object(resolver, "tokenizer_path", mock_tokenizer_path):
                paths = resolver._find_model_paths()
                assert paths[0] is not None

    def test_get_query_resolver(self):
        """Test getting query resolver."""
        resolver = get_query_resolver()
        assert resolver is not None
        assert resolver.model_name == "e5-small"

    def test_get_element_resolver(self):
        """Test getting element resolver."""
        resolver = get_element_resolver()
        assert resolver is not None
        assert resolver.model_name == "markuplm-base"

    def test_resolver_normalize_embedding(self):
        """Test embedding normalization."""
        resolver = ONNXModelResolver("test-model")

        # Create a non-normalized vector
        vec = np.array([3.0, 4.0])
        normalized = resolver._normalize_embedding(vec)

        # Check it's normalized (magnitude = 1)
        magnitude = np.linalg.norm(normalized)
        assert abs(magnitude - 1.0) < 0.001

    def test_resolver_deterministic_embedding(self):
        """Test deterministic embedding generation."""
        resolver = ONNXModelResolver("test-model")

        text = "test input"
        emb1 = resolver._generate_deterministic_embedding(text)
        emb2 = resolver._generate_deterministic_embedding(text)

        # Same text should give same embedding
        np.testing.assert_array_equal(emb1, emb2)

        # Different text should give different embedding
        emb3 = resolver._generate_deterministic_embedding("different")
        assert not np.array_equal(emb1, emb3)

    @patch("onnxruntime.InferenceSession")
    def test_resolver_with_onnx_model(self, mock_session_class):
        """Test resolver with mocked ONNX model."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock model outputs
        mock_session.run.return_value = [np.random.randn(1, 384)]
        mock_session.get_inputs.return_value = [
            Mock(name="input_ids"),
            Mock(name="attention_mask"),
        ]

        with patch("her.embeddings._resolve.Path") as mock_path:
            mock_model_path = Mock()
            mock_model_path.exists.return_value = True

            with patch.object(ONNXModelResolver, "_find_model_paths") as mock_find:
                mock_find.return_value = (mock_model_path, mock_model_path)

                resolver = ONNXModelResolver("test-model")
                resolver.session = mock_session

                # Test embedding with model
                embedding = resolver.embed("test text")
                assert isinstance(embedding, np.ndarray)
                mock_session.run.assert_called()
