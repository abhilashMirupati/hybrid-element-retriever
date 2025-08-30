#!/usr/bin/env python3
"""Test all HER components individually and as an integrated framework."""
# import sys
# from pathlib import Path
# removed sys.path hack
print("=" * 80)
print("COMPREHENSIVE COMPONENT ANALYSIS - HER FRAMEWORK")
print("=" * 80)

# Component inventory
components = []

# 1. Core Pipeline
try:
    from her.pipeline import HERPipeline
    pipeline = HERPipeline()
    components.append(("HERPipeline", "✓", "Core orchestrator"))
except Exception as e:
    components.append(("HERPipeline", "✗", str(e)))

# 2. Intent Parser
try:
    from her.parser.intent import IntentParser
    parser = IntentParser()
    test_intent = parser.parse("click the submit button")
    works = test_intent.action is not None
    components.append(("IntentParser", "✓" if works else "✗", "NLP intent extraction"))
except Exception as e:
    components.append(("IntentParser", "✗", str(e)))

# 3. Query Embedder
try:
    from her.embeddings.query_embedder import QueryEmbedder
    qe = QueryEmbedder()
    embedding = qe.embed("test query")
    works = embedding is not None and len(embedding) > 0
    components.append(("QueryEmbedder", "✓" if works else "✗", "Query vectorization"))
except Exception as e:
    components.append(("QueryEmbedder", "✗", str(e)))

# 4. Element Embedder
try:
    from her.embeddings.element_embedder import ElementEmbedder
    ee = ElementEmbedder()
    elem = {"tag": "button", "text": "Submit"}
    embedding = ee.embed(elem)
    works = embedding is not None and len(embedding) > 0
    components.append(("ElementEmbedder", "✓" if works else "✗", "Element vectorization"))
except Exception as e:
    components.append(("ElementEmbedder", "✗", str(e)))

# 5. Fusion Scorer
try:
    from her.rank.fusion_scorer import FusionScorer
    fs = FusionScorer()
    score = fs.score([0.1]*384, [0.1]*768, {"text": "test"}, {})
    works = isinstance(score, (int, float))
    components.append(("FusionScorer", "✓" if works else "✗", "Multi-signal scoring"))
except Exception as e:
    components.append(("FusionScorer", "✗", str(e)))

# 6. Locator Synthesizer
try:
    from her.locator.synthesize import LocatorSynthesizer
    ls = LocatorSynthesizer()
    locs = ls.synthesize({"tag": "button", "id": "btn1", "text": "Click"})
    works = len(locs) > 0 and isinstance(locs[0], str)
    components.append(("LocatorSynthesizer", "✓" if works else "✗", "XPath/CSS generation"))
except Exception as e:
    components.append(("LocatorSynthesizer", "✗", str(e)))

# 7. Session Manager
try:
    from her.session.manager import SessionManager
    sm = SessionManager()
    components.append(("SessionManager", "✓", "Basic session handling"))
except Exception as e:
    components.append(("SessionManager", "✗", str(e)))

# 8. Enhanced Session Manager
try:
    from her.session.enhanced_manager import EnhancedSessionManager
    esm = EnhancedSessionManager()
    components.append(("EnhancedSessionManager", "✓", "Advanced session features"))
except Exception as e:
    components.append(("EnhancedSessionManager", "✗", str(e)))

# 9. Two-Tier Cache
try:
    from her.cache.two_tier import TwoTierCache
    cache = TwoTierCache()
    cache.put("test", "value")
    works = cache.get("test") == "value"
    components.append(("TwoTierCache", "✓" if works else "✗", "LRU + persistent cache"))
except Exception as e:
    components.append(("TwoTierCache", "✗", str(e)))

# 10. SQLite Cache
try:
    from her.vectordb.sqlite_cache import SQLiteKV
    db = SQLiteKV("/tmp/test.db")
    db.put("key", b"value")
    works = db.get("key") == b"value"
    components.append(("SQLiteKV", "✓" if works else "✗", "Persistent storage"))
except Exception as e:
    components.append(("SQLiteKV", "✗", str(e)))

# 11. FAISS Store
try:
    from her.vectordb.faiss_store import FAISSStore
    store = FAISSStore(dimension=384)
    components.append(("FAISSStore", "✓", "Vector similarity search"))
except Exception as e:
    components.append(("FAISSStore", "✗", str(e)))

# 12. Action Executor
try:
    from her.actions import ActionExecutor, ActionResult
    # Can't test without page, but check structure
    components.append(("ActionExecutor", "✓", "Browser action execution"))
except Exception as e:
    components.append(("ActionExecutor", "✗", str(e)))

# 13. Snapshot Manager
try:
    from her.session.snapshot import SnapshotManager
    snap = SnapshotManager()
    components.append(("SnapshotManager", "✓", "DOM snapshot + SPA tracking"))
except Exception as e:
    components.append(("SnapshotManager", "✗", str(e)))

# 14. Resilience Manager
try:
    from her.resilience import ResilienceManager
    rm = ResilienceManager()
    components.append(("ResilienceManager", "✓", "Error recovery"))
except Exception as e:
    components.append(("ResilienceManager", "✗", str(e)))

# 15. Validators
try:
    from her.validators import InputValidator, DOMValidator, FormValidator
    iv = InputValidator()
    dv = DOMValidator()
    fv = FormValidator()
    components.append(("Validators", "✓", "Input/DOM/Form validation"))
except Exception as e:
    components.append(("Validators", "✗", str(e)))

# 16. Enhanced Verifier
try:
    from her.locator.enhanced_verify import EnhancedVerifier
    verifier = EnhancedVerifier()
    components.append(("EnhancedVerifier", "✓", "Self-healing verification"))
except Exception as e:
    components.append(("EnhancedVerifier", "✗", str(e)))

# 17. CLI API
try:
    from her.cli_api import HybridElementRetrieverClient
    client = HybridElementRetrieverClient()
    components.append(("HybridClient", "✓", "Main API interface"))
except Exception as e:
    components.append(("HybridClient", "✗", str(e)))

# Print component status
print("\n1. COMPONENT INVENTORY")
print("-" * 80)
print(f"{'Component':<25} {'Status':<8} {'Description'}")
print("-" * 80)
for name, status, desc in components:
    print(f"{name:<25} {status:<8} {desc}")

working = sum(1 for _, s, _ in components if s == "✓")
total = len(components)
print(f"\nWorking: {working}/{total} ({working*100/total:.1f}%)")

# Test integration points
print("\n2. INTEGRATION TESTING")
print("-" * 80)

integration_tests = []

# Test 1: Pipeline → Synthesizer
try:
    desc = {"tag": "button", "text": "Test", "id": "btn1"}
    xpath, fallbacks = pipeline._generate_xpath(desc)
    integration_tests.append(("Pipeline → Synthesizer", "✓" if xpath else "✗"))
except Exception as e:
    integration_tests.append(("Pipeline → Synthesizer", "✗"))

# Test 2: Pipeline → Embedders
try:
    candidates = pipeline._semantic_match("click button", [desc], {"action": "click"})
    integration_tests.append(("Pipeline → Embedders", "✓" if candidates else "✗"))
except Exception as e:
    integration_tests.append(("Pipeline → Embedders", "✗"))

# Test 3: Cache integration
try:
    cache_key = "test_key"
    pipeline.cache.put(cache_key, {"test": "data"})
    retrieved = pipeline.cache.get(cache_key)
    integration_tests.append(("Pipeline → Cache", "✓" if retrieved else "✗"))
except Exception as e:
    integration_tests.append(("Pipeline → Cache", "✗"))

# Test 4: Full flow
try:
    result = pipeline.process("click the button", [desc])
    has_xpath = result and "xpath" in result and result["xpath"]
    integration_tests.append(("Full Pipeline Flow", "✓" if has_xpath else "✗"))
except Exception as e:
    integration_tests.append(("Full Pipeline Flow", "✗"))

print(f"{'Integration Point':<30} {'Status'}")
print("-" * 80)
for test, status in integration_tests:
    print(f"{test:<30} {status}")

# Performance testing
print("\n3. PERFORMANCE METRICS")
print("-" * 80)

import time

# Test XPath generation speed
descriptors = [
    {"tag": "button", "text": f"Button {i}", "id": f"btn{i}"}
    for i in range(100)
]

start = time.time()
for desc in descriptors[:10]:
    ls.synthesize(desc)
elapsed = time.time() - start
print(f"XPath generation (10 elements): {elapsed*1000:.2f}ms ({elapsed*100:.2f}ms/element)")

# Test semantic matching speed
start = time.time()
pipeline._semantic_match("click button", descriptors, {"action": "click"})
elapsed = time.time() - start
print(f"Semantic match (100 elements): {elapsed*1000:.2f}ms")

# Test full pipeline speed
start = time.time()
result = pipeline.process("click button 5", descriptors[:20])
elapsed = time.time() - start
print(f"Full pipeline (20 elements): {elapsed*1000:.2f}ms")

print("\n4. ACCURACY TESTING")
print("-" * 80)

# Test cases for accuracy
test_cases = [
    # (descriptors, query, expected_match)
    (
        [
            {"tag": "button", "text": "Submit", "id": "form1-submit"},
            {"tag": "button", "text": "Submit", "id": "form2-submit"}
        ],
        "click form2 submit",
        "form2-submit"
    ),
    (
        [
            {"tag": "input", "type": "email", "placeholder": "Email"},
            {"tag": "input", "type": "password", "placeholder": "Password"}
        ],
        "enter email",
        "email"
    ),
    (
        [
            {"tag": "a", "text": "Home", "href": "/"},
            {"tag": "a", "text": "About", "href": "/about"}
        ],
        "go to about page",
        "about"
    )
]

correct = 0
for descs, query, expected in test_cases:
    result = pipeline.process(query, descs)
    if result and result.get("element"):
        elem = result["element"]
        # Check if expected text is in any field
        found = any(
            expected.lower() in str(v).lower()
            for v in elem.values()
        )
        if found:
            correct += 1
            print(f"✓ '{query}' → found '{expected}'")
        else:
            print(f"✗ '{query}' → wrong element")
    else:
        print(f"✗ '{query}' → no result")

accuracy = correct / len(test_cases) * 100
print(f"\nAccuracy: {correct}/{len(test_cases)} ({accuracy:.1f}%)")

print("\n" + "=" * 80)
print("COMPONENT HEALTH SUMMARY")
print("=" * 80)

# Identify issues
issues = []

if working < total:
    failed = [name for name, status, _ in components if status == "✗"]
    issues.append(f"Failed components: {', '.join(failed)}")

if accuracy < 100:
    issues.append(f"Accuracy below 100%: {accuracy:.1f}%")

failed_integrations = [test for test, status in integration_tests if status == "✗"]
if failed_integrations:
    issues.append(f"Failed integrations: {', '.join(failed_integrations)}")

if issues:
    print("ISSUES FOUND:")
    for issue in issues:
        print(f"  • {issue}")
else:
    print("✅ All components working at 100%")

print("\nRECOMMENDATIONS:")
if accuracy < 100:
    print("  • Semantic matching needs improvement - move from rule-based to learned approach")
if working < total:
    print("  • Fix non-working components")
print("  • Consider using transformer-based matching instead of rule-based scoring")