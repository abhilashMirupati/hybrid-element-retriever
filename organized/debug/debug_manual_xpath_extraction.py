#!/usr/bin/env python3
"""
Manual XPath extraction for each step in each canonical mode.
This will help us see what XPaths are being generated for each step.
"""

import os
import subprocess
import re
from src.her.runner import Runner

def get_xpaths_for_mode(mode):
    """Get XPaths for each step in a specific mode"""
    print(f"\n{'='*60}")
    print(f"🔍 EXTRACTING XPaths for MODE: {mode}")
    print(f"{'='*60}")
    
    # Set environment variable
    os.environ['HER_CANONICAL_MODE'] = mode
    
    try:
        # Create runner and navigate to page
        runner = Runner(headless=True)
        runner._ensure_browser()
        runner._page.goto('https://www.verizon.com/')
        
        # Get initial snapshot
        snapshot = runner._inline_snapshot()
        elements = snapshot.get('elements', [])
        
        print(f"📊 Total elements captured: {len(elements)}")
        
        # Test each step manually to get XPaths
        steps = [
            "Click on featured smartphones menu list in top",
            "Select Apple filter", 
            "Select iPhone 16 Pro on us: Buy now",
            "Validate it landed on https://www.verizon.com/smartphones/apple-iphone-16-pro/",
            "Select Desert Titanium",
            "Select 512 GB",
            "Click Add to Cart",
            "Validate 'Added to your cart'"
        ]
        
        step_xpaths = []
        
        for i, step in enumerate(steps, 1):
            print(f"\n--- Step {i}: {step} ---")
            
            try:
                # Use the runner's internal method to find elements
                result = runner._find_elements(step, user_intent=step)
                
                if result and 'candidates' in result:
                    candidates = result['candidates']
                    if candidates:
                        best_candidate = candidates[0]
                        xpath = best_candidate.get('xpath', 'No XPath found')
                        text = best_candidate.get('text', 'No text')
                        tag = best_candidate.get('tag', 'No tag')
                        interactive = best_candidate.get('interactive', False)
                        
                        print(f"   ✅ Found element:")
                        print(f"      XPath: {xpath}")
                        print(f"      Text: '{text}'")
                        print(f"      Tag: {tag}")
                        print(f"      Interactive: {interactive}")
                        
                        step_xpaths.append({
                            'step': step,
                            'xpath': xpath,
                            'text': text,
                            'tag': tag,
                            'interactive': interactive
                        })
                    else:
                        print(f"   ❌ No candidates found")
                        step_xpaths.append({
                            'step': step,
                            'xpath': 'No candidates found',
                            'text': '',
                            'tag': '',
                            'interactive': False
                        })
                else:
                    print(f"   ❌ No result from _find_elements")
                    step_xpaths.append({
                        'step': step,
                        'xpath': 'No result',
                        'text': '',
                        'tag': '',
                        'interactive': False
                    })
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                step_xpaths.append({
                    'step': step,
                    'xpath': f'Error: {e}',
                    'text': '',
                    'tag': '',
                    'interactive': False
                })
        
        runner._close()
        return step_xpaths
        
    except Exception as e:
        print(f"❌ Error in mode {mode}: {e}")
        return []

def main():
    """Main execution"""
    print("🚀 Manual XPath extraction for all canonical modes")
    
    modes = ['DOM_ONLY', 'ACCESSIBILITY_ONLY', 'BOTH']
    all_results = {}
    
    for mode in modes:
        step_xpaths = get_xpaths_for_mode(mode)
        all_results[mode] = step_xpaths
    
    # Summary
    print(f"\n{'='*80}")
    print("📋 XPath SUMMARY FOR ALL MODES")
    print(f"{'='*80}")
    
    for mode, step_xpaths in all_results.items():
        print(f"\n--- {mode} ---")
        for i, step_data in enumerate(step_xpaths, 1):
            print(f"Step {i}: {step_data['step']}")
            print(f"  XPath: {step_data['xpath']}")
            print(f"  Text: '{step_data['text']}'")
            print(f"  Tag: {step_data['tag']} | Interactive: {step_data['interactive']}")
            print()

if __name__ == "__main__":
    main()