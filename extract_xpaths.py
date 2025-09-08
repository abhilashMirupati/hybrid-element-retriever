#!/usr/bin/env python3
"""
Extract XPaths from test results for each canonical mode
"""

import json
import re

def extract_xpaths_from_json(results_file):
    """Extract XPaths from the test results JSON file"""
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    print("🔍 XPath Analysis for All Canonical Modes")
    print("=" * 60)
    
    for result in results:
        mode = result['mode']
        print(f"\n--- {mode} ---")
        
        # Extract XPaths from stdout
        stdout = result.get('stdout', '')
        
        # Look for step-specific XPaths
        step_pattern = r'Step \d+: (.+?)\n.*?selector=([^\s\n]+)'
        step_matches = re.findall(step_pattern, stdout, re.DOTALL)
        
        if step_matches:
            print("📍 Step-by-Step XPaths:")
            for i, (step_desc, xpath) in enumerate(step_matches, 1):
                print(f"  Step {i}: {step_desc.strip()}")
                print(f"    XPath: {xpath}")
        else:
            print("❌ No step-specific XPaths found")
        
        # Look for all XPaths in the output
        all_xpath_patterns = [
            r'selector=([^\s\n]+)',
            r'XPath: ([^\s\n]+)',
            r'xpath=([^\s\n]+)'
        ]
        
        all_xpaths = []
        for pattern in all_xpath_patterns:
            matches = re.findall(pattern, stdout)
            all_xpaths.extend(matches)
        
        # Remove duplicates and filter out invalid XPaths
        unique_xpaths = []
        for xpath in set(all_xpaths):
            if xpath and not xpath.startswith('{') and len(xpath) > 5:
                unique_xpaths.append(xpath)
        
        if unique_xpaths:
            print(f"\n📋 All XPaths found ({len(unique_xpaths)}):")
            for xpath in unique_xpaths[:10]:  # Show first 10
                print(f"    {xpath}")
            if len(unique_xpaths) > 10:
                print(f"    ... and {len(unique_xpaths) - 10} more")
        else:
            print("❌ No valid XPaths found")
        
        print(f"\n⏱️  Duration: {result.get('duration', 0):.1f}s")
        print(f"✅ Success: {result.get('success', False)}")

if __name__ == "__main__":
    extract_xpaths_from_json('/workspace/test_results_20250907_235452.json')