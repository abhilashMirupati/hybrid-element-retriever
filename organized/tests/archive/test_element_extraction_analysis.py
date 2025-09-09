#!/usr/bin/env python3
"""
Comprehensive Node Analysis Script
Tests all CDP modes and analyzes node extraction completeness
"""

import os
import time
from playwright.sync_api import sync_playwright
from her.runner import run_steps
from her.config import CanonicalMode

def analyze_cdp_modes():
    """Analyze all CDP modes and node extraction"""
    
    print("🔬 COMPREHENSIVE CDP NODE ANALYSIS")
    print("=" * 60)
    
    modes = [
        (CanonicalMode.DOM_ONLY, "DOM Only"),
        (CanonicalMode.ACCESSIBILITY_ONLY, "Accessibility Only"), 
        (CanonicalMode.BOTH, "Both DOM + Accessibility")
    ]
    
    results = {}
    
    for mode, mode_name in modes:
        print(f"\n📋 TESTING: {mode_name}")
        print("-" * 40)
        
        # Set environment variable
        os.environ['HER_CANONICAL_MODE'] = mode.value
        
        try:
            # Test with a simple page first
            steps = ['Open https://www.google.com/', 'Wait for page load']
            
            start_time = time.time()
            result = run_steps(steps, headless=True)
            duration = time.time() - start_time
            
            # Extract node count from the result
            if hasattr(result, 'elements') and result.elements:
                node_count = len(result.elements)
            else:
                node_count = 0
                
            results[mode_name] = {
                'success': True,
                'node_count': node_count,
                'duration': duration,
                'error': None
            }
            
            print(f"✅ {mode_name}: {node_count} nodes in {duration:.2f}s")
            
        except Exception as e:
            results[mode_name] = {
                'success': False,
                'node_count': 0,
                'duration': 0,
                'error': str(e)
            }
            print(f"❌ {mode_name}: FAILED - {str(e)}")
    
    return results

def test_direct_cdp_extraction():
    """Test direct CDP extraction to get raw node counts"""
    
    print("\n🔍 DIRECT CDP EXTRACTION TEST")
    print("=" * 60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto('https://www.google.com/')
            page.wait_for_load_state('networkidle')
            
            # Get DOM node count
            dom_count = page.evaluate("""
                () => {
                    const allElements = document.querySelectorAll('*');
                    return allElements.length;
                }
            """)
            
            # Get accessibility tree count
            try:
                ax_tree = page.accessibility.snapshot()
                ax_count = count_accessibility_nodes(ax_tree)
            except Exception as e:
                ax_count = 0
                print(f"⚠️  Accessibility tree extraction failed: {e}")
            
            print(f"📊 RAW NODE COUNTS:")
            print(f"   DOM Elements: {dom_count}")
            print(f"   Accessibility Nodes: {ax_count}")
            print(f"   Total Potential: {dom_count + ax_count}")
            
            browser.close()
            
            return {
                'dom_count': dom_count,
                'ax_count': ax_count,
                'total_potential': dom_count + ax_count
            }
            
        except Exception as e:
            print(f"❌ Direct CDP test failed: {e}")
            browser.close()
            return None

def count_accessibility_nodes(node, count=0):
    """Recursively count accessibility tree nodes"""
    if not node:
        return count
    
    count += 1
    
    if 'children' in node and node['children']:
        for child in node['children']:
            count = count_accessibility_nodes(child, count)
    
    return count

def analyze_canonical_building():
    """Analyze canonical building process"""
    
    print("\n🏗️  CANONICAL BUILDING ANALYSIS")
    print("=" * 60)
    
    # Test with BOTH mode for comprehensive analysis
    os.environ['HER_CANONICAL_MODE'] = 'both'
    
    try:
        steps = ['Open https://www.google.com/', 'Wait for page load']
        result = run_steps(steps, headless=True)
        
        if hasattr(result, 'elements') and result.elements:
            elements = result.elements
            
            # Analyze element types
            tag_counts = {}
            attr_counts = {}
            interactive_count = 0
            
            for element in elements:
                tag = element.get('tag', 'unknown')
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                attrs = element.get('attrs', {})
                attr_count = len(attrs)
                attr_counts[attr_count] = attr_counts.get(attr_count, 0) + 1
                
                # Check if interactive
                if tag.lower() in ['button', 'input', 'select', 'textarea', 'a']:
                    interactive_count += 1
                elif attrs.get('role') in ['button', 'link', 'textbox', 'combobox']:
                    interactive_count += 1
            
            print(f"📊 CANONICAL BUILDING STATS:")
            print(f"   Total Elements: {len(elements)}")
            print(f"   Interactive Elements: {interactive_count}")
            print(f"   Non-Interactive Elements: {len(elements) - interactive_count}")
            
            print(f"\n📋 TOP 10 ELEMENT TYPES:")
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            for tag, count in sorted_tags[:10]:
                print(f"   {tag}: {count}")
            
            print(f"\n📊 ATTRIBUTE DISTRIBUTION:")
            sorted_attrs = sorted(attr_counts.items(), key=lambda x: x[0])
            for attr_count, element_count in sorted_attrs[:10]:
                print(f"   {attr_count} attributes: {element_count} elements")
            
            return {
                'total_elements': len(elements),
                'interactive_elements': interactive_count,
                'tag_distribution': tag_counts,
                'attr_distribution': attr_counts
            }
        else:
            print("❌ No elements found in result")
            return None
            
    except Exception as e:
        print(f"❌ Canonical building analysis failed: {e}")
        return None

def main():
    """Main analysis function"""
    
    print("🚀 Starting Comprehensive CDP Node Analysis")
    print("=" * 60)
    
    # Test 1: CDP Modes Analysis
    cdp_results = analyze_cdp_modes()
    
    # Test 2: Direct CDP Extraction
    raw_counts = test_direct_cdp_extraction()
    
    # Test 3: Canonical Building Analysis
    canonical_stats = analyze_canonical_building()
    
    # Summary
    print("\n📊 SUMMARY")
    print("=" * 60)
    
    print("CDP MODES PERFORMANCE:")
    for mode_name, result in cdp_results.items():
        if result['success']:
            print(f"   ✅ {mode_name}: {result['node_count']} nodes ({result['duration']:.2f}s)")
        else:
            print(f"   ❌ {mode_name}: FAILED - {result['error']}")
    
    if raw_counts:
        print(f"\nRAW NODE COUNTS:")
        print(f"   DOM Elements: {raw_counts['dom_count']}")
        print(f"   Accessibility Nodes: {raw_counts['ax_count']}")
        print(f"   Total Potential: {raw_counts['total_potential']}")
    
    if canonical_stats:
        print(f"\nCANONICAL BUILDING:")
        print(f"   Total Elements Processed: {canonical_stats['total_elements']}")
        print(f"   Interactive Elements: {canonical_stats['interactive_elements']}")
        print(f"   Non-Interactive Elements: {canonical_stats['total_elements'] - canonical_stats['interactive_elements']}")
    
    print("\n✅ Analysis Complete!")

if __name__ == "__main__":
    main()