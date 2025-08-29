#!/usr/bin/env python3
"""Test that the fixes actually work."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("=" * 80)
print("TESTING FIXES")
print("=" * 80)

# 1. Test Intent Parser Fix
print("\n1. INTENT PARSER FIX")
print("-" * 80)

from her.parser.intent import IntentParser
parser = IntentParser()

test_queries = [
    ("search for products", "search"),
    ("find items", "find"),
    ("look for shoes", "look"),
    ("navigate to home", "navigate"),
    ("scroll down", "scroll"),
    ("hover over menu", "hover")
]

fixed_count = 0
for query, expected in test_queries:
    intent = parser.parse(query)
    if intent.action == expected or expected in intent.action:
        fixed_count += 1
        print(f"✅ '{query}' → {intent.action}")
    else:
        print(f"❌ '{query}' → {intent.action} (expected {expected})")

print(f"\nIntent parser: {fixed_count}/{len(test_queries)} working")

# 2. Test XPath Generation Fixes
print("\n2. XPATH GENERATION FIXES")
print("-" * 80)

from her.locator.synthesize import LocatorSynthesizer
synthesizer = LocatorSynthesizer()

edge_cases = [
    {"tag": "a", "href": "javascript:void(0)", "text": "Click me", "id": "js-link"},
    {"tag": "div", "class": "class1 class2 class3"},
    {"tag": "input", "type": "", "name": "field"},
    {"tag": "svg", "id": "icon-svg"},
    {"tag": "svg:path", "d": "M10 10"}
]

xpath_fixed = 0
for element in edge_cases:
    try:
        xpaths = synthesizer.synthesize(element.copy())  # Use copy to avoid mutation
        if xpaths and len(xpaths) > 0:
            xpath_fixed += 1
            print(f"✅ Generated XPath for {element.get('tag', 'unknown')}: {xpaths[0]}")
        else:
            print(f"❌ No XPath for {element}")
    except Exception as e:
        print(f"❌ Failed on {element.get('tag')}: {e}")

print(f"\nXPath generation: {xpath_fixed}/{len(edge_cases)} working")

# 3. Test Full Pipeline with Fixes
print("\n3. FULL PIPELINE WITH FIXES")
print("-" * 80)

from her.pipeline import HERPipeline as FinalProductionPipeline
pipeline = FinalProductionPipeline()

# Test cases that previously failed
test_cases = [
    # Intent parsing
    ("search for products", [{"tag": "input", "type": "search", "placeholder": "Search..."}]),
    ("find items", [{"tag": "button", "text": "Find"}]),
    
    # XPath edge cases
    ("click link", [{"tag": "a", "href": "javascript:void(0)", "text": "Click"}]),
    ("click icon", [{"tag": "svg", "class": "icon"}]),
    
    # Multiple classes
    ("click button", [{"tag": "button", "class": "btn btn-primary btn-large", "text": "Submit"}]),
]

pipeline_fixed = 0
for query, elements in test_cases:
    try:
        result = pipeline.process(query, elements)
        if result and result.xpath:
            pipeline_fixed += 1
            print(f"✅ '{query}' → {result.xpath}")
        else:
            print(f"❌ '{query}' → No XPath")
    except Exception as e:
        print(f"❌ '{query}' failed: {e}")

print(f"\nPipeline: {pipeline_fixed}/{len(test_cases)} working")

# 4. Summary
print("\n" + "=" * 80)
print("FIX VERIFICATION SUMMARY")
print("=" * 80)

total_tests = len(test_queries) + len(edge_cases) + len(test_cases)
total_fixed = fixed_count + xpath_fixed + pipeline_fixed

print(f"\nTotal: {total_fixed}/{total_tests} tests passing ({total_fixed*100/total_tests:.1f}%)")

print("\nImprovements:")
print(f"• Intent parser: {fixed_count}/{len(test_queries)} actions recognized")
print(f"• XPath generation: {xpath_fixed}/{len(edge_cases)} edge cases handled")
print(f"• Pipeline integration: {pipeline_fixed}/{len(test_cases)} queries working")

if total_fixed == total_tests:
    print("\n🎉 ALL FIXES WORKING!")
else:
    print(f"\n⚠️ {total_tests - total_fixed} issues remain")