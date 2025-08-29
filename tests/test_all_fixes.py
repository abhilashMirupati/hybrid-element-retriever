#!/usr/bin/env python3
"""Test all fixes: thread-safe cache, real embeddings, and complex features."""

import sys
import time
import threading
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("=" * 80)
print("TESTING ALL FIXES")
print("=" * 80)

# 1. TEST THREAD-SAFE CACHE
print("\n1. THREAD-SAFE CACHE TEST")
print("-" * 80)

from her.cache.thread_safe_cache import ThreadSafeTwoTierCache

cache = ThreadSafeTwoTierCache()
results = []
errors = []

def cache_worker(worker_id, iterations=100):
    """Worker thread for cache testing."""
    try:
        for i in range(iterations):
            key = f"key_{worker_id}_{i}"
            value = f"value_{worker_id}_{i}"
            
            # Write
            cache.put(key, value)
            
            # Read
            retrieved = cache.get(key)
            if retrieved != value:
                errors.append(f"Worker {worker_id}: Mismatch at {i}")
            
            # Also try reading other workers' keys
            other_key = f"key_{(worker_id + 1) % 5}_{i}"
            cache.get(other_key)  # Should not crash
            
        results.append(f"Worker {worker_id}: Completed {iterations} operations")
    except Exception as e:
        errors.append(f"Worker {worker_id}: {e}")

# Start multiple threads
threads = []
for i in range(5):
    t = threading.Thread(target=cache_worker, args=(i, 50))
    threads.append(t)
    t.start()

# Wait for all threads
for t in threads:
    t.join()

print(f"Threads completed: {len(results)}/5")
if errors:
    print(f"❌ Errors: {len(errors)}")
    for err in errors[:3]:
        print(f"  - {err}")
else:
    print("✅ No errors - cache is thread-safe!")

stats = cache.get_stats()
print(f"Cache stats: {stats}")

# 2. TEST REAL EMBEDDINGS
print("\n2. REAL EMBEDDINGS TEST")
print("-" * 80)

from her.embeddings.real_embedder import MiniLMEmbedder, MarkupLMEmbedder

# Test MiniLM
minilm = MiniLMEmbedder()
query_emb1 = minilm.embed_text("click submit button")
query_emb2 = minilm.embed_text("click submit button")  # Same text
query_emb3 = minilm.embed_text("enter email address")  # Different text

print(f"MiniLM embedding dimension: {len(query_emb1)}")
print(f"Deterministic: {query_emb1[:5] == query_emb2[:5]}")  # Should be True
print(f"Different for different text: {query_emb1[:5] != query_emb3[:5]}")  # Should be True

# Test MarkupLM
markuplm = MarkupLMEmbedder()
elem1 = {"tag": "button", "text": "Submit", "id": "btn1"}
elem2 = {"tag": "input", "type": "email", "name": "email"}

elem_emb1 = markuplm.embed_element(elem1)
elem_emb2 = markuplm.embed_element(elem2)

print(f"\nMarkupLM embedding dimension: {len(elem_emb1)}")
print(f"Different for different elements: {elem_emb1[:5] != elem_emb2[:5]}")

# Calculate similarity
def cosine_similarity(v1, v2):
    """Calculate cosine similarity between vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = sum(a * a for a in v1) ** 0.5
    mag2 = sum(b * b for b in v2) ** 0.5
    if mag1 * mag2 == 0:
        return 0
    return dot / (mag1 * mag2)

# Test semantic similarity
similar_queries = [
    ("click button", "press button"),
    ("enter email", "type email"),
    ("submit form", "send form")
]

print("\nSemantic similarity test:")
for q1, q2 in similar_queries:
    emb1 = minilm.embed_text(q1)
    emb2 = minilm.embed_text(q2)
    sim = cosine_similarity(emb1, emb2)
    print(f"  '{q1}' vs '{q2}': {sim:.3f}")

# 3. TEST FINAL PIPELINE WITH ALL FEATURES
print("\n3. FINAL PIPELINE TEST")
print("-" * 80)

from her.pipeline import HERPipeline as FinalProductionPipeline

pipeline = FinalProductionPipeline()

# Test basic functionality
test_cases = [
    (
        "click submit button",
        [{"tag": "button", "text": "Submit", "id": "submit-btn"}],
        "submit-btn"
    ),
    (
        "enter email",
        [
            {"tag": "input", "type": "text", "name": "username"},
            {"tag": "input", "type": "email", "name": "email"}
        ],
        "email"
    ),
    (
        "add phone to cart",
        [
            {"tag": "button", "text": "Add to Cart", "dataTestId": "add-laptop"},
            {"tag": "button", "text": "Add to Cart", "dataTestId": "add-phone"}
        ],
        "phone"
    )
]

def test_pipeline_accuracy():
    """Test pipeline accuracy on test cases."""
    success = 0
    for query, elements, expected in test_cases:
        result = pipeline.process(query, elements)
        if result and "element" in result:
            elem_str = str(result["element"]).lower()
            if expected.lower() in elem_str:
                print(f"✅ '{query}' → correct")
                success += 1
            else:
                print(f"❌ '{query}' → wrong")
    
    print(f"Pipeline accuracy: {success}/{len(test_cases)}")
    assert success >= len(test_cases) * 0.8  # At least 80% accuracy

# Run the test
test_pipeline_accuracy()

# Test cache hit
print("\nTesting cache hits...")
start = time.time()
result1 = pipeline.process("test query", [{"tag": "div"}])
time1 = time.time() - start

start = time.time()
result2 = pipeline.process("test query", [{"tag": "div"}])
time2 = time.time() - start

if result2.cache_hit and time2 < time1 * 0.5:
    print(f"✅ Cache hit working: {time1*1000:.1f}ms → {time2*1000:.1f}ms")
else:
    print(f"❌ Cache not working properly")

# Get cache statistics
cache_stats = pipeline.get_cache_stats()
print(f"Pipeline cache stats: {cache_stats}")

# 4. TEST FRAME AND SHADOW DOM WITH FINAL PIPELINE
print("\n4. COMPLEX FEATURES WITH FINAL PIPELINE")
print("-" * 80)

# Test with frame metadata
frame_elements = [
    {"tag": "button", "text": "Main Button", "id": "main-btn", "frame": "main"},
    {"tag": "button", "text": "Frame Button", "id": "frame-btn", "frame": "iframe1"},
    {"tag": "input", "type": "email", "name": "email", "frame": "iframe2"}
]

frame_result = pipeline.process("click frame button", frame_elements)
if frame_result.xpath and "frame:" in frame_result.xpath:
    print(f"✅ Frame context in XPath: {frame_result.xpath}")
else:
    print(f"⚠️ Frame context missing: {frame_result.xpath}")

# Test with shadow DOM
shadow_elements = [
    {"tag": "button", "text": "Light Button", "id": "light-btn"},
    {"tag": "button", "text": "Shadow Button", "id": "shadow-btn", "inShadowRoot": True, "shadowHost": "my-component"}
]

shadow_result = pipeline.process("click shadow button", shadow_elements)
if shadow_result.xpath and "shadow:" in shadow_result.xpath:
    print(f"✅ Shadow DOM context in XPath: {shadow_result.xpath}")
else:
    print(f"⚠️ Shadow DOM context missing: {shadow_result.xpath}")

# 5. FINAL SUMMARY
print("\n" + "=" * 80)
print("ALL FIXES VERIFICATION")
print("=" * 80)

all_tests = {
    "Thread-safe cache": len(errors) == 0,
    "Real embeddings": len(query_emb1) == 384,
    "Deterministic embeddings": query_emb1[:5] == query_emb2[:5],
    "Pipeline accuracy": success == len(test_cases),
    "Cache hits": result2.cache_hit,
    "Frame support": "frame:" in frame_result.xpath if frame_result.xpath else False,
    "Shadow DOM support": "shadow:" in shadow_result.xpath if shadow_result.xpath else False
}

passed = sum(1 for v in all_tests.values() if v)
total = len(all_tests)

print(f"\nResults: {passed}/{total} features working")
for feature, working in all_tests.items():
    status = "✅" if working else "❌"
    print(f"  {status} {feature}")

if passed == total:
    print("\n🎉 ALL ISSUES FIXED!")
else:
    print(f"\n⚠️ {total - passed} issues remain")