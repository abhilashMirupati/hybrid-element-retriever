#!/usr/bin/env python3
"""
Comprehensive Pipeline Debug Script
Shows detailed input/output logging for all steps in the HER pipeline
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, Any, List

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from her.runner import Runner
from her.config import get_config
from her.parser.enhanced_intent import EnhancedIntentParser

def print_section(title: str, width: int = 80):
    """Print a formatted section header"""
    print(f"\n{'=' * width}")
    print(f"🔍 {title}")
    print(f"{'=' * width}")

def print_step(step_name: str, data: Any, max_length: int = 200):
    """Print a step with formatted data"""
    print(f"\n📋 {step_name}:")
    print("-" * 60)
    
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and len(value) > max_length:
                print(f"   {key}: {value[:max_length]}... (truncated, length: {len(value)})")
            else:
                print(f"   {key}: {value}")
    elif isinstance(data, list):
        print(f"   List with {len(data)} items:")
        for i, item in enumerate(data[:5]):  # Show first 5 items
            if isinstance(item, dict):
                print(f"     [{i}] {item}")
            else:
                print(f"     [{i}] {item}")
        if len(data) > 5:
            print(f"     ... and {len(data) - 5} more items")
    else:
        print(f"   {data}")

def debug_dom_snapshot(runner: Runner, url: str) -> Dict[str, Any]:
    """Debug DOM snapshot process"""
    print_section("DOM SNAPSHOT PROCESS")
    
    print(f"🌐 URL: {url}")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    
    # Capture snapshot
    start_time = time.time()
    snapshot = runner._snapshot(url)
    snapshot_time = time.time() - start_time
    
    print(f"✅ Snapshot completed in {snapshot_time:.3f}s")
    print(f"   Total elements: {len(snapshot.get('elements', []))}")
    print(f"   Frame URL: {snapshot.get('url', 'N/A')}")
    print(f"   Frame hash: {snapshot.get('frame_hash', 'N/A')}")
    
    # Analyze element types
    elements = snapshot.get('elements', [])
    element_types = {}
    for el in elements:
        tag = el.get('tag', 'unknown')
        element_types[tag] = element_types.get(tag, 0) + 1
    
    print(f"   Element type distribution: {element_types}")
    
    # Show sample elements
    print(f"\n📝 Sample Elements (first 3):")
    for i, el in enumerate(elements[:3]):
        print(f"   Element {i+1}:")
        print(f"     Tag: {el.get('tag', 'N/A')}")
        print(f"     Text: '{el.get('text', '')[:50]}...'")
        print(f"     BackendNodeId: {el.get('backendNodeId', 'N/A')}")
        print(f"     XPath: {el.get('xpath', 'N/A')}")
        print(f"     Attributes: {len(el.get('attrs', {}))} attrs")
    
    return snapshot

def debug_intent_parsing(query: str) -> Dict[str, Any]:
    """Debug intent parsing process"""
    print_section("INTENT PARSING PROCESS")
    
    print(f"🔍 Query: '{query}'")
    
    # Parse intent
    start_time = time.time()
    parser = EnhancedIntentParser()
    parsed = parser.parse(query)
    parse_time = time.time() - start_time
    
    print(f"✅ Intent parsing completed in {parse_time:.3f}s")
    print(f"   Action: {parsed.action}")
    print(f"   Target: {parsed.target_phrase}")
    print(f"   Value: {parsed.value}")
    print(f"   Confidence: {parsed.confidence}")
    
    return parsed

def debug_element_selection(runner: Runner, query: str, snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Debug element selection process"""
    print_section("ELEMENT SELECTION PROCESS")
    
    print(f"🔍 Query: '{query}'")
    print(f"   Available elements: {len(snapshot.get('elements', []))}")
    
    # Resolve selector
    start_time = time.time()
    result = runner._resolve_selector(query, snapshot)
    selection_time = time.time() - start_time
    
    print(f"✅ Element selection completed in {selection_time:.3f}s")
    print(f"   Strategy: {result.get('strategy', 'unknown')}")
    print(f"   Confidence: {result.get('confidence', 0.0):.3f}")
    print(f"   Selected XPath: {result.get('selector', 'N/A')}")
    print(f"   Element text: {result.get('meta', {}).get('text', 'N/A')}")
    print(f"   Element tag: {result.get('meta', {}).get('tag', 'N/A')}")
    print(f"   Candidates found: {len(result.get('candidates', []))}")
    
    # Show top candidates
    candidates = result.get('candidates', [])
    if candidates:
        print(f"\n🏆 Top 5 Candidates:")
        for i, candidate in enumerate(candidates[:5]):
            print(f"   {i+1}. Score: {candidate.get('score', 0.0):.3f}")
            print(f"      XPath: {candidate.get('xpath', 'N/A')}")
            print(f"      Text: '{candidate.get('text', '')[:50]}...'")
            print(f"      Tag: {candidate.get('tag', 'N/A')}")
    
    return result

def debug_text_extraction(snapshot: Dict[str, Any]) -> None:
    """Debug text extraction process"""
    print_section("TEXT EXTRACTION ANALYSIS")
    
    elements = snapshot.get('elements', [])
    print(f"📊 Analyzing text extraction for {len(elements)} elements")
    
    # Find elements with text
    text_elements = [el for el in elements if el.get('text', '').strip()]
    print(f"   Elements with text: {len(text_elements)}")
    
    # Find elements with duplicated text
    duplicated_elements = []
    for el in text_elements:
        text = el.get('text', '')
        if text.count(' ') > 0 and len(set(text.split())) < len(text.split()):
            duplicated_elements.append(el)
    
    print(f"   Elements with potential duplication: {len(duplicated_elements)}")
    
    if duplicated_elements:
        print(f"\n⚠️  Duplicated Text Examples:")
        for i, el in enumerate(duplicated_elements[:3]):
            print(f"   {i+1}. Tag: {el.get('tag', 'N/A')}")
            print(f"      Text: '{el.get('text', '')}'")
            print(f"      XPath: {el.get('xpath', 'N/A')}")
    
    # Find elements with accessibility data
    ax_elements = [el for el in elements if 'accessibility' in el]
    print(f"   Elements with accessibility data: {len(ax_elements)}")
    
    # Find elements with DOM data
    dom_elements = [el for el in elements if 'attrs' in el]
    print(f"   Elements with DOM attributes: {len(dom_elements)}")

def debug_hierarchy_context(snapshot: Dict[str, Any]) -> None:
    """Debug hierarchy context building"""
    print_section("HIERARCHY CONTEXT ANALYSIS")
    
    elements = snapshot.get('elements', [])
    print(f"📊 Analyzing hierarchy context for {len(elements)} elements")
    
    # Check if hierarchy context is present
    context_elements = [el for el in elements if 'context' in el]
    print(f"   Elements with hierarchy context: {len(context_elements)}")
    
    if context_elements:
        print(f"\n🌳 Sample Hierarchy Context:")
        for i, el in enumerate(context_elements[:3]):
            context = el.get('context', {})
            print(f"   Element {i+1}:")
            print(f"     Tag: {el.get('tag', 'N/A')}")
            print(f"     Text: '{el.get('text', '')[:30]}...'")
            print(f"     Hierarchy Path: {context.get('hierarchy_path', 'N/A')}")
            print(f"     Depth: {context.get('depth', 'N/A')}")
            print(f"     Has Children: {context.get('has_children', 'N/A')}")
    else:
        print("   ⚠️  No hierarchy context found - hierarchy may be disabled")

def main():
    """Main debug function"""
    print_section("COMPREHENSIVE HER PIPELINE DEBUG", 100)
    print(f"🚀 Starting comprehensive pipeline debug")
    print(f"⏰ Start time: {datetime.now().isoformat()}")
    
    # Set up environment
    os.environ['HER_CANONICAL_MODE'] = 'both'
    os.environ['HER_USE_HIERARCHY'] = 'true'
    os.environ['HER_USE_TWO_STAGE'] = 'true'
    
    # Initialize runner
    print_section("RUNNER INITIALIZATION")
    start_time = time.time()
    runner = Runner()
    init_time = time.time() - start_time
    print(f"✅ Runner initialized in {init_time:.3f}s")
    
    # Test URL and query
    test_url = "https://www.verizon.com/"
    test_query = "Click on the Shop button"
    
    try:
        # Step 1: DOM Snapshot
        snapshot = debug_dom_snapshot(runner, test_url)
        
        # Step 2: Intent Parsing
        parsed_intent = debug_intent_parsing(test_query)
        
        # Step 3: Text Extraction Analysis
        debug_text_extraction(snapshot)
        
        # Step 4: Hierarchy Context Analysis
        debug_hierarchy_context(snapshot)
        
        # Step 5: Element Selection
        result = debug_element_selection(runner, test_query, snapshot)
        
        # Final Summary
        print_section("FINAL SUMMARY", 100)
        print(f"🎯 Query: '{test_query}'")
        print(f"🌐 URL: {test_url}")
        print(f"📊 Total elements processed: {len(snapshot.get('elements', []))}")
        print(f"🎯 Selected element: {result.get('selector', 'N/A')}")
        print(f"📈 Confidence: {result.get('confidence', 0.0):.3f}")
        print(f"🔧 Strategy: {result.get('strategy', 'unknown')}")
        print(f"⏱️  Total processing time: {time.time() - start_time:.3f}s")
        
        print(f"\n✅ DEBUG COMPLETED SUCCESSFULLY")
        
    except Exception as e:
        print(f"\n❌ ERROR during debug: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print_section("CLEANUP")
        try:
            runner.cleanup_models()
            runner._browser.close()
            runner._playwright.stop()
            print("✅ Cleanup completed")
        except Exception as e:
            print(f"⚠️  Cleanup error: {e}")

if __name__ == "__main__":
    main()