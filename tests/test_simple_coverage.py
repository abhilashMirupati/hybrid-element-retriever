"""Simple tests to improve code coverage."""
from unittest.mock import Mock, patch, MagicMock
import pytest
import numpy as np

# Test imports and basic functionality
def test_imports():
    """Test that all modules can be imported."""
    from her import __init__
    from her.bridge import cdp_bridge, snapshot
    from her.embeddings import _resolve, cache, element_embedder, query_embedder
    from her.executor import actions
    from her.locator import synthesize, verify
    from her.parser import intent
    from her.rank import fusion, heuristics
    from her.recovery import promotion, self_heal
    from her.session import manager
    from her.vectordb import faiss_store
    assert True


def test_config_functions():
    """Test config functions."""
    from her.config import get_models_dir, get_embeddings_cache_dir, get_promotion_store_path
    
    models_dir = get_models_dir()
    assert models_dir is not None
    
    cache_dir = get_embeddings_cache_dir()
    assert cache_dir is not None
    
    store_path = get_promotion_store_path()
    assert store_path is not None


def test_bridge_functions_mocked():
    """Test bridge functions with mocks."""
    from her.bridge.cdp_bridge import get_flattened_document, get_full_ax_tree
    
    # Test with None page
    assert get_flattened_document(None) == []
    assert get_full_ax_tree(None) == []


def test_snapshot_functions():
    """Test snapshot functions."""
    from her.bridge.snapshot import compute_dom_hash, detect_dom_change
    
    # Test hash computation
    descriptors = [{"tagName": "div", "text": "Hello"}]
    hash1 = compute_dom_hash(descriptors)
    assert len(hash1) == 64  # SHA256 hash length
    
    # Test change detection
    assert detect_dom_change(hash1, hash1) is False
    assert detect_dom_change(hash1, "different") is True


def test_parser_functions():
    """Test parser functions."""
    from her.parser.intent import IntentParser
    
    parser = IntentParser()
    
    # Test basic parsing
    intent = parser.parse("click the button")
    assert intent["action"] in ["click", "press", "tap"]
    assert "button" in intent["target"]
    
    # Test batch parsing
    intents = parser.parse_batch(["click button", "type hello"])
    assert len(intents) == 2


def test_heuristic_functions():
    """Test heuristic functions."""
    from her.rank.heuristics import heuristic_score, rank_by_heuristics
    
    descriptor = {
        "tagName": "button",
        "text": "Submit",
        "attributes": {"type": "submit"}
    }
    
    score = heuristic_score(descriptor, "submit button")
    assert score > 0
    
    descriptors = [descriptor, {"tagName": "div", "text": "Hello"}]
    ranked = rank_by_heuristics(descriptors, "submit")
    assert len(ranked) > 0


def test_locator_functions():
    """Test locator functions."""
    from her.locator.synthesize import LocatorSynthesizer
    
    synth = LocatorSynthesizer()
    
    descriptor = {
        "tagName": "button",
        "attributes": {"id": "submit-btn"},
        "text": "Submit"
    }
    
    locators = synth.synthesize(descriptor)
    assert len(locators) > 0
    assert any("#submit-btn" in loc for loc in locators)


def test_verify_functions():
    """Test verify functions."""
    from her.locator.verify import LocatorVerifier
    
    verifier = LocatorVerifier()
    
    # Test with no page
    result = verifier.verify("button", None)
    assert result["unique"] is False
    assert result["count"] == 0


def test_self_heal_functions():
    """Test self-heal functions."""
    from her.recovery.self_heal import SelfHealer, HealingStrategy
    
    healer = SelfHealer()
    assert healer is not None
    
    # Test healing strategy
    strategy = HealingStrategy()
    assert strategy.name == "base"


def test_promotion_functions():
    """Test promotion functions."""
    from her.recovery.promotion import PromotionStore, PromotionRecord
    
    # Use in-memory store for testing
    store = PromotionStore(use_sqlite=False)
    
    # Test promotion
    store.promote("button#submit", "http://example.com")
    score = store.get_promotion_score("button#submit", "http://example.com")
    assert score > 0
    
    # Test record
    record = PromotionRecord(
        locator="button",
        context="test",
        success_count=5,
        failure_count=1
    )
    assert record.success_count == 5


def test_faiss_store():
    """Test FAISS vector store."""
    from her.vectordb.faiss_store import InMemoryVectorStore
    
    store = InMemoryVectorStore(dim=128)
    assert store.dim == 128
    assert store.size() == 0
    
    # Add a vector
    vec = np.random.randn(128).astype(np.float32)
    metadata = {"id": 1}
    store.add(vec, metadata)
    assert store.size() == 1


def test_cache_functions():
    """Test cache functions."""
    from her.embeddings.cache import EmbeddingCache
    
    cache = EmbeddingCache(capacity=10)
    assert cache.capacity == 10
    
    # Test put and get
    key = "test_key"
    value = np.array([1, 2, 3])
    cache.put(key, value)
    
    retrieved = cache.get(key)
    assert retrieved is not None
    np.testing.assert_array_equal(retrieved, value)


def test_element_embedder_cache():
    """Test element embedder caching."""
    from her.embeddings.element_embedder import ElementEmbedder
    
    embedder = ElementEmbedder(cache_enabled=True)
    assert embedder.cache is not None
    
    embedder_no_cache = ElementEmbedder(cache_enabled=False)
    assert embedder_no_cache.cache is None


def test_query_embedder_cache():
    """Test query embedder caching."""
    from her.embeddings.query_embedder import QueryEmbedder
    
    embedder = QueryEmbedder(cache_enabled=True)
    assert embedder.cache is not None
    
    embedder_no_cache = QueryEmbedder(cache_enabled=False)
    assert embedder_no_cache.cache is None