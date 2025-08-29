#!/usr/bin/env python3
"""Validate production readiness of HER."""

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from her.pipeline_production import ProductionPipeline
from her.scoring.fusion_scorer_v2 import FusionScorerV2

print("=" * 80)
print("HER PRODUCTION VALIDATION")
print("=" * 80)

# Initialize components
pipeline = ProductionPipeline()
scorer = FusionScorerV2()

# Track results
checklist = {}

# Phase 1: Core Flow Tests
print("\nPhase 1: Core Flow Validation")
print("-" * 80)

# Test 1: Cold Start
print("\n1. Cold Start Flow")
dom = [
    {"tag": "button", "text": "Submit", "id": "btn1"},
    {"tag": "input", "type": "email", "placeholder": "Email"}
]
start = time.time()
result = pipeline.process("click submit", dom)
cold_start_time = (time.time() - start) * 1000

checklist["Cold Start"] = (
    result.xpath != "" and 
    result.confidence > 0.5 and
    cold_start_time < 3000
)
print(f"  ✅ DOM snapshot + embeddings: {cold_start_time:.1f}ms" if checklist["Cold Start"] else "  ❌ Failed")

# Test 2: Incremental Updates
print("\n2. Incremental Updates")
dom.append({"tag": "button", "text": "Cancel", "id": "btn2"})
start = time.time()
result = pipeline.process("click cancel", dom)
incremental_time = (time.time() - start) * 1000

checklist["Incremental Updates"] = (
    result.xpath != "" and
    incremental_time < cold_start_time  # Should be faster
)
print(f"  ✅ Delta detection + partial embed: {incremental_time:.1f}ms" if checklist["Incremental Updates"] else "  ❌ Failed")

# Test 3: User Intent Parsing
print("\n3. User Intent Parsing")
test_intents = [
    ("click the submit button", "click"),
    ("type my email address", "type"),
    ("search for products", "search")
]

intent_success = True
for query, expected_action in test_intents:
    intent = pipeline.intent_parser.parse(query)
    if intent.action != expected_action:
        intent_success = False
        print(f"  ❌ Failed: '{query}' → {intent.action} (expected {expected_action})")

checklist["Intent Parsing"] = intent_success
if intent_success:
    print("  ✅ All intents parsed correctly")

# Phase 2: Semantic Matching Tests
print("\n\nPhase 2: Semantic Matching & Scoring")
print("-" * 80)

# Test 4: Product Disambiguation
print("\n4. Product Disambiguation")
product_dom = [
    {"tag": "button", "text": "Add to Cart", "dataTestId": "add-laptop"},
    {"tag": "button", "text": "Add to Cart", "dataTestId": "add-phone"},
    {"tag": "button", "text": "Add to Cart", "dataTestId": "add-tablet"}
]

tests_passed = 0
test_cases = [
    ("add phone to cart", "phone"),
    ("add laptop to cart", "laptop"),
    ("add tablet to cart", "tablet")
]

for query, expected in test_cases:
    result = pipeline.process(query, product_dom)
    if expected in result.element.get("dataTestId", "").lower():
        tests_passed += 1
        print(f"  ✅ '{query}' → {expected}")
    else:
        print(f"  ❌ '{query}' → wrong product")

checklist["Product Disambiguation"] = tests_passed == len(test_cases)

# Test 5: Form Field Disambiguation
print("\n5. Form Field Disambiguation")
form_dom = [
    {"tag": "input", "type": "email", "name": "email", "placeholder": "Email"},
    {"tag": "input", "type": "password", "name": "password", "placeholder": "Password"},
    {"tag": "input", "type": "text", "name": "username", "placeholder": "Username"}
]

tests_passed = 0
test_cases = [
    ("enter email", "email"),
    ("type password", "password"),
    ("enter username", "text")  # username has type="text"
]

for query, expected_type in test_cases:
    result = pipeline.process(query, form_dom)
    if result.element.get("type") == expected_type or expected_type in result.element.get("name", ""):
        tests_passed += 1
        print(f"  ✅ '{query}' → {expected_type} field")
    else:
        print(f"  ❌ '{query}' → wrong field")

checklist["Form Fields"] = tests_passed == len(test_cases)

# Test 6: Action Disambiguation
print("\n6. Action Disambiguation")
action_dom = [
    {"tag": "button", "text": "Submit Form", "dataTestId": "submit-btn"},
    {"tag": "button", "text": "Search", "dataTestId": "search-btn"},
    {"tag": "button", "text": "Cancel", "dataTestId": "cancel-btn"}
]

tests_passed = 0
test_cases = [
    ("submit form", "submit"),
    ("search", "search"),
    ("cancel", "cancel")
]

for query, expected in test_cases:
    result = pipeline.process(query, action_dom)
    if expected in result.element.get("dataTestId", "").lower():
        tests_passed += 1
        print(f"  ✅ '{query}' → {expected} button")
    else:
        print(f"  ❌ '{query}' → wrong button")

checklist["Actions"] = tests_passed == len(test_cases)

# Phase 3: Pipeline Features
print("\n\nPhase 3: Pipeline Features")
print("-" * 80)

# Test 7: XPath Generation
print("\n7. XPath Generation")
test_element = {"tag": "button", "dataTestId": "test-btn", "id": "btn1", "text": "Click Me"}
result = pipeline.process("click button", [test_element])

xpath_quality = (
    result.xpath != "" and
    ("data-testid" in result.xpath.lower() or "test-btn" in result.xpath) and
    len(result.fallbacks) > 0
)

checklist["XPath Generation"] = xpath_quality
print(f"  ✅ Primary: {result.xpath}" if xpath_quality else "  ❌ Poor quality XPath")
if result.fallbacks:
    print(f"  ✅ Fallbacks: {len(result.fallbacks)} alternatives")

# Test 8: Caching
print("\n8. Caching")
query = "click submit"
dom = [{"tag": "button", "text": "Submit"}]

# First call
result1 = pipeline.process(query, dom)
time1 = result1.processing_time_ms

# Second call (cached)
result2 = pipeline.process(query, dom)
time2 = result2.processing_time_ms

cache_working = (
    result2.cache_hit and
    time2 < time1 * 0.5 and
    result1.xpath == result2.xpath
)

checklist["Caching"] = cache_working
print(f"  ✅ Cache hit, {time1:.1f}ms → {time2:.1f}ms" if cache_working else "  ❌ Cache not working")

# Test 9: Edge Cases
print("\n9. Edge Cases")
edge_cases_passed = 0

# Unicode
result = pipeline.process("点击提交", [{"tag": "button", "text": "提交"}])
if result.confidence > 0:
    edge_cases_passed += 1
    print("  ✅ Unicode handled")
else:
    print("  ❌ Unicode failed")

# Empty query
result = pipeline.process("", [{"tag": "button", "text": "Click"}])
if result.confidence == 0:
    edge_cases_passed += 1
    print("  ✅ Empty query handled")
else:
    print("  ❌ Empty query not handled")

# Duplicate labels
dup_dom = [
    {"tag": "button", "text": "Submit", "id": "btn1"},
    {"tag": "button", "text": "Submit", "id": "btn2"}
]
result = pipeline.process("click btn2 submit", dup_dom)
if "btn2" in result.element.get("id", ""):
    edge_cases_passed += 1
    print("  ✅ Duplicate labels disambiguated")
else:
    print("  ❌ Duplicate labels failed")

checklist["Edge Cases"] = edge_cases_passed == 3

# Phase 4: Performance
print("\n\nPhase 4: Performance Benchmarks")
print("-" * 80)

# Generate larger DOM
large_dom = []
for i in range(100):
    large_dom.append({
        "tag": "button" if i % 2 == 0 else "input",
        "text": f"Element {i}",
        "id": f"elem{i}",
        "dataTestId": f"test-elem-{i}"
    })

# Measure performance
times = []
for i in range(5):
    start = time.time()
    result = pipeline.process(f"click element {i*20}", large_dom)
    times.append((time.time() - start) * 1000)

avg_time = sum(times) / len(times)
max_time = max(times)

checklist["Performance"] = avg_time < 100 and max_time < 500
print(f"  Average: {avg_time:.1f}ms")
print(f"  Max: {max_time:.1f}ms")
print(f"  {'✅' if checklist['Performance'] else '❌'} Meets benchmarks")

# Final Summary
print("\n" + "=" * 80)
print("PRODUCTION READINESS CHECKLIST")
print("=" * 80)

total_passed = sum(1 for v in checklist.values() if v)
total_tests = len(checklist)
percentage = (total_passed / total_tests) * 100

for item, passed in checklist.items():
    status = "✅" if passed else "❌"
    print(f"{status} {item}")

print("\n" + "-" * 80)
print(f"Score: {total_passed}/{total_tests} ({percentage:.1f}%)")

if percentage >= 95:
    print("\n🎉 PRODUCTION READY - All critical flows validated!")
elif percentage >= 80:
    print("\n⚠️ NEARLY READY - Minor issues to fix")
else:
    print("\n❌ NOT READY - Significant issues found")

# Detailed scoring accuracy
print("\n" + "=" * 80)
print("SCORING ACCURACY VALIDATION")
print("=" * 80)

# Test specific scoring scenarios
test_scenarios = [
    # (query, elements, expected_index)
    (
        "add phone to cart",
        [
            {"tag": "button", "text": "Add to Cart", "dataTestId": "add-laptop"},
            {"tag": "button", "text": "Add to Cart", "dataTestId": "add-phone"}
        ],
        1  # Should select phone (index 1)
    ),
    (
        "enter email",
        [
            {"tag": "input", "type": "text", "name": "username"},
            {"tag": "input", "type": "email", "name": "email"}
        ],
        1  # Should select email (index 1)
    ),
    (
        "submit form",
        [
            {"tag": "button", "text": "Cancel"},
            {"tag": "button", "text": "Submit", "type": "submit"}
        ],
        1  # Should select submit (index 1)
    )
]

scoring_correct = 0
for query, elements, expected_idx in test_scenarios:
    result = pipeline.process(query, elements)
    actual_element = result.element
    expected_element = elements[expected_idx]
    
    if actual_element == expected_element:
        scoring_correct += 1
        print(f"✅ '{query}' → Correct element selected")
    else:
        print(f"❌ '{query}' → Wrong element selected")
        print(f"   Expected: {expected_element}")
        print(f"   Got: {actual_element}")

scoring_accuracy = (scoring_correct / len(test_scenarios)) * 100
print(f"\nScoring Accuracy: {scoring_accuracy:.1f}%")

if scoring_accuracy >= 95:
    print("✅ Scoring accuracy exceeds 95% threshold")
else:
    print(f"❌ Scoring accuracy {scoring_accuracy:.1f}% below 95% threshold")

print("\n" + "=" * 80)