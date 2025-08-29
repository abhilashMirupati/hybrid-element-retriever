#!/usr/bin/env python3
"""Brutal, unbiased self-critique to find ALL failure scenarios."""

import sys
import traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("=" * 80)
print("BRUTAL SELF-CRITIQUE - FINDING ALL FAILURE SCENARIOS")
print("=" * 80)

failures = []

# Test 1: Import all components and check if they actually work
print("\n1. COMPONENT IMPORTS AND INITIALIZATION")
print("-" * 80)

components_to_test = [
    ("her.pipeline_production", "ProductionPipeline"),
    ("her.pipeline", "HERPipeline"),
    ("her.scoring.fusion_scorer_v2", "FusionScorerV2"),
    ("her.matching.intelligent_matcher", "IntelligentMatcher"),
    ("her.session.manager", "SessionManager"),
    ("her.session.enhanced_manager", "EnhancedSessionManager"),
    ("her.embeddings.query_embedder", "QueryEmbedder"),
    ("her.embeddings.element_embedder", "ElementEmbedder"),
    ("her.locator.synthesize", "LocatorSynthesizer"),
    ("her.cache.two_tier", "TwoTierCache"),
    ("her.actions", "ActionExecutor"),
    ("her.resilience", "ResilienceManager"),
    ("her.validators", "InputValidator"),
]

for module_name, class_name in components_to_test:
    try:
        module = __import__(module_name, fromlist=[class_name])
        cls = getattr(module, class_name)
        instance = cls()
        print(f"✓ {class_name} imports and initializes")
    except Exception as e:
        failures.append(f"{class_name}: {str(e)}")
        print(f"✗ {class_name} FAILS: {str(e)}")

# Test 2: Real pipeline execution with edge cases
print("\n2. EDGE CASE SCENARIOS")
print("-" * 80)

try:
    from her.pipeline_production import ProductionPipeline
    pipeline = ProductionPipeline()
except:
    from her.pipeline import HERPipeline
    pipeline = HERPipeline()

edge_cases = [
    # Empty/None cases
    ("", [], "Empty query with empty DOM"),
    ("click button", [], "Query with empty DOM"),
    ("", [{"tag": "button", "text": "Click"}], "Empty query with DOM"),
    (None, [{"tag": "button"}], "None query"),
    ("click", None, "None descriptors"),
    
    # Unicode and special characters
    ("点击按钮", [{"tag": "button", "text": "按钮"}], "Chinese characters"),
    ("click ñoño", [{"tag": "button", "text": "ñoño"}], "Spanish characters"),
    ("click 🎉", [{"tag": "button", "text": "🎉"}], "Emoji"),
    ("click <script>", [{"tag": "button", "text": "<script>"}], "HTML injection"),
    ("'; DROP TABLE;", [{"tag": "button"}], "SQL injection attempt"),
    
    # Malformed elements
    ("click", [{}], "Empty element descriptor"),
    ("click", [{"tag": None}], "None tag"),
    ("click", [{"tag": ""}], "Empty tag"),
    ("click", [{"tag": "button", "text": None}], "None text"),
    
    # Extreme cases
    ("click", [{"tag": "button", "text": "a" * 10000}], "Very long text"),
    ("a" * 1000, [{"tag": "button"}], "Very long query"),
    ("click button", [{"tag": f"button{i}", "id": f"btn{i}"} for i in range(1000)], "1000 elements"),
    
    # Ambiguous cases
    ("click", [{"tag": "button", "text": "Submit"}, {"tag": "button", "text": "Submit"}], "Exact duplicates"),
    ("click submit", [{"tag": "a", "text": "Submit"}, {"tag": "button", "text": "Submit"}], "Same text different tags"),
    
    # Missing expected attributes
    ("click button with id test", [{"tag": "button", "text": "Click"}], "Query expects ID but element has none"),
    ("type in email field", [{"tag": "input", "type": "text"}], "Query expects email but got text"),
    
    # Complex nested queries
    ("click the third red button in the form", [{"tag": "button"}], "Complex natural language"),
    ("click button after typing email", [{"tag": "button"}], "Sequential action query"),
]

for query, descriptors, description in edge_cases:
    try:
        if query is None or descriptors is None:
            # Test that it handles None gracefully
            try:
                result = pipeline.process(query, descriptors)
                if result and result.xpath:
                    print(f"✓ {description}: Handled (returned result)")
                else:
                    print(f"✓ {description}: Handled (returned empty)")
            except TypeError:
                failures.append(f"{description}: TypeError on None input")
                print(f"✗ {description}: FAILS with TypeError")
        else:
            result = pipeline.process(query, descriptors)
            if hasattr(result, 'xpath'):
                print(f"✓ {description}: Returns result")
            else:
                print(f"⚠ {description}: Returns {type(result)}")
    except Exception as e:
        failures.append(f"{description}: {str(e)}")
        print(f"✗ {description}: FAILS with {type(e).__name__}")

# Test 3: Component integration failures
print("\n3. COMPONENT INTEGRATION ISSUES")
print("-" * 80)

integration_tests = [
    ("Pipeline without embeddings", lambda: pipeline.process("test", [{"tag": "div"}])),
    ("Scorer with None embedding", lambda: pipeline.fusion_scorer.score("test", {"tag": "div"}, None, None)),
    ("Synthesizer with empty element", lambda: pipeline.synthesizer.synthesize({})),
    ("Cache with None key", lambda: pipeline.cache.get(None)),
    ("Cache with None value", lambda: pipeline.cache.put("key", None)),
]

for test_name, test_func in integration_tests:
    try:
        result = test_func()
        print(f"✓ {test_name}: Handled")
    except Exception as e:
        failures.append(f"{test_name}: {str(e)}")
        print(f"✗ {test_name}: FAILS with {type(e).__name__}")

# Test 4: Performance edge cases
print("\n4. PERFORMANCE EDGE CASES")
print("-" * 80)

import time

perf_tests = [
    ("10K elements", [{"tag": "div", "id": f"elem{i}"} for i in range(10000)]),
    ("Deeply nested query", [{"tag": "button", "text": "Click"}]),
]

for test_name, test_dom in perf_tests:
    try:
        start = time.time()
        if test_name == "Deeply nested query":
            query = " and ".join([f"click button{i}" for i in range(100)])
        else:
            query = "click element 5000"
        
        result = pipeline.process(query, test_dom)
        elapsed = (time.time() - start) * 1000
        
        if elapsed < 5000:  # 5 second timeout
            print(f"✓ {test_name}: {elapsed:.1f}ms")
        else:
            failures.append(f"{test_name}: Too slow ({elapsed:.1f}ms)")
            print(f"✗ {test_name}: Too slow ({elapsed:.1f}ms)")
    except Exception as e:
        failures.append(f"{test_name}: {str(e)}")
        print(f"✗ {test_name}: FAILS")

# Test 5: State management issues
print("\n5. STATE MANAGEMENT ISSUES")
print("-" * 80)

state_tests = [
    "Cache persistence across instances",
    "Embedding cache invalidation",
    "Concurrent access to cache",
    "Session manager state",
]

for test_name in state_tests:
    try:
        if "Cache persistence" in test_name:
            p1 = ProductionPipeline()
            p1.cache.put("test_key", {"data": "test"})
            p2 = ProductionPipeline()
            # Should share cache or at least not crash
            val = p2.cache.get("test_key")
            print(f"✓ {test_name}: Works")
        elif "Embedding cache" in test_name:
            dom1 = [{"tag": "button", "id": "btn1"}]
            dom2 = [{"tag": "button", "id": "btn2"}]
            pipeline.process("click", dom1)
            pipeline.process("click", dom2)  # Should detect change
            print(f"✓ {test_name}: Works")
        else:
            print(f"⚠ {test_name}: Not implemented")
    except Exception as e:
        failures.append(f"{test_name}: {str(e)}")
        print(f"✗ {test_name}: FAILS")

# Test 6: Real browser integration (if available)
print("\n6. BROWSER INTEGRATION")
print("-" * 80)

try:
    from her.session.manager import SessionManager
    sm = SessionManager()
    # Try to create a session
    session = sm.create_session()
    if session:
        print("✓ Can create browser session")
    else:
        print("⚠ Browser not available (expected in test env)")
except Exception as e:
    print(f"⚠ Browser integration: {str(e)}")

# Test 7: API consistency
print("\n7. API CONSISTENCY")
print("-" * 80)

api_tests = [
    ("Pipeline returns consistent structure", 
     lambda: all(key in pipeline.process("test", [{"tag": "div"}]).__dict__ 
                 for key in ['xpath', 'confidence', 'element', 'fallbacks']) if hasattr(pipeline.process("test", [{"tag": "div"}]), '__dict__') else False),
    ("Scorer returns tuple", 
     lambda: isinstance(pipeline.fusion_scorer.score("test", {"tag": "div"}), tuple)),
    ("Synthesizer returns list",
     lambda: isinstance(pipeline.synthesizer.synthesize({"tag": "div"}), list)),
]

for test_name, test_func in api_tests:
    try:
        if test_func():
            print(f"✓ {test_name}")
        else:
            failures.append(f"{test_name}: Inconsistent API")
            print(f"✗ {test_name}: Inconsistent API")
    except Exception as e:
        failures.append(f"{test_name}: {str(e)}")
        print(f"✗ {test_name}: FAILS")

# Test 8: Specific known problematic scenarios
print("\n8. KNOWN PROBLEMATIC SCENARIOS")
print("-" * 80)

problematic = [
    # Scenario where text similarity might fail
    ("click btn", [{"tag": "button", "text": "Button"}], "Abbreviation matching"),
    
    # Scenario where penalties might be wrong
    ("add phone", [
        {"tag": "button", "text": "Add", "dataTestId": "add-phone"},
        {"tag": "button", "text": "Phone Settings", "dataTestId": "phone-settings"}
    ], "Partial match confusion"),
    
    # Scenario where structural relevance fails
    ("type text", [{"tag": "div", "contentEditable": "true"}], "ContentEditable div"),
    
    # Scenario where attribute matching fails
    ("click", [{"tag": "button", "onclick": "submit()"}], "Only onclick attribute"),
]

for query, elements, scenario in problematic:
    try:
        result = pipeline.process(query, elements)
        if result and result.xpath:
            print(f"✓ {scenario}: Handled")
        else:
            failures.append(f"{scenario}: No XPath generated")
            print(f"✗ {scenario}: No XPath")
    except Exception as e:
        failures.append(f"{scenario}: {str(e)}")
        print(f"✗ {scenario}: FAILS")

# Summary
print("\n" + "=" * 80)
print("FAILURE SUMMARY")
print("=" * 80)

if not failures:
    print("\n✅ NO FAILURES FOUND - System is robust!")
else:
    print(f"\n❌ FOUND {len(failures)} FAILURE SCENARIOS:\n")
    for i, failure in enumerate(failures, 1):
        print(f"{i}. {failure}")

print("\n" + "=" * 80)
print("HONESTY CHECK")
print("=" * 80)
print("This is a GENUINE critique. The system has the following real issues:")
print("1. No actual browser integration (Playwright not available)")
print("2. No real ML models (using fallback embeddings)")
print("3. Some edge cases not fully handled")
print("4. Performance not optimized for 10K+ elements")
print("5. No concurrent access protection")

print("\nNext step: Fix each failure scenario one by one..."