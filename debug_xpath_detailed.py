#!/usr/bin/env python3
"""
Debug script to see what XPath candidates are being generated
"""

import os
import sys
import time
import logging
from playwright.sync_api import sync_playwright

# Add src to path
sys.path.insert(0, '/workspace/src')

# Set environment variables
os.environ["HER_USE_SEMANTIC_SEARCH"] = "false"
os.environ["HER_DEBUG"] = "true"

from her.core.runner import Runner
from her.locator.enhanced_no_semantic import EnhancedNoSemanticMatcher
from her.locator.xpath_validator import XPathValidator
from her.locator.hierarchical_context import HierarchicalContextBuilder

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def debug_xpath_generation():
    """Debug XPath generation step by step"""
    
    print("=" * 80)
    print("DEBUGGING XPATH GENERATION")
    print("=" * 80)
    
    try:
        # Initialize runner and take snapshot
        print("\n1. Initializing runner and taking snapshot...")
        runner = Runner()
        snapshot = runner._snapshot("https://www.verizon.com")
        elements = snapshot.get('elements', [])
        print(f"Found {len(elements)} elements on page")
        
        # Get the page from runner
        runner_page = runner._ensure_browser()
        
        # Test with "Shop" which we know has matches
        test_query = "Click on 'Shop'"
        print(f"\n2. Testing with query: {test_query}")
        
        # Initialize matcher
        matcher = EnhancedNoSemanticMatcher()
        
        # Parse intent
        parsed_intent = matcher.intent_parser.parse_step(test_query)
        print(f"Parsed intent: {parsed_intent.intent}, target: {parsed_intent.target_text}")
        
        # Apply critical fixes
        fixed_elements = matcher.critical_fixes.apply_all_fixes(elements, parsed_intent)
        print(f"Applied critical fixes, elements count: {len(fixed_elements)}")
        
        # Find exact matches
        exact_matches = matcher.core_matcher.find_exact_matches(fixed_elements, parsed_intent)
        print(f"Found {len(exact_matches)} exact matches")
        
        if exact_matches:
            # Show first few matches
            for i, match in enumerate(exact_matches[:3]):
                print(f"  Match {i+1}: {match.element.get('tag', '')} - '{match.element.get('text', '')[:50]}...'")
        
        # Apply intent heuristics
        heuristically_scored_matches = matcher.core_matcher.apply_intent_heuristics(exact_matches, parsed_intent)
        
        # Apply intent integration scoring
        intent_scored_matches = matcher.intent_integration.apply_intent_scoring(heuristically_scored_matches, parsed_intent)
        
        # Build hierarchical context for top matches
        top_matches = intent_scored_matches[:5]
        print(f"\n3. Building hierarchical context for {len(top_matches)} top matches...")
        
        contexts = matcher.context_builder.build_contexts([m.match for m in top_matches], fixed_elements)
        print(f"Built {len(contexts)} hierarchical contexts")
        
        # Generate XPath candidates
        print(f"\n4. Generating XPath candidates...")
        xpath_validator = XPathValidator()
        xpath_candidates = xpath_validator.generate_candidates(contexts)
        print(f"Generated {len(xpath_candidates)} XPath candidates")
        
        # Show the generated XPath candidates
        for i, candidate in enumerate(xpath_candidates):
            print(f"\n  Candidate {i+1} ({candidate.strategy}):")
            print(f"    XPath: {candidate.xpath}")
            element_text = candidate.element.get('text', '')
            print(f"    Element: {candidate.element.get('tag', '')} - '{element_text}'")
            print(f"    Full element: {candidate.element}")
            print(f"    Confidence: {candidate.confidence}")
        
        # Validate XPath candidates
        print(f"\n5. Validating XPath candidates...")
        validated_candidates = xpath_validator.validate_candidates(xpath_candidates, runner_page)
        
        valid_count = len([c for c in validated_candidates if c.is_valid])
        print(f"Validated {valid_count} valid XPath candidates out of {len(validated_candidates)}")
        
        # Show validation results
        for i, candidate in enumerate(validated_candidates):
            print(f"\n  Candidate {i+1} validation:")
            print(f"    XPath: {candidate.xpath}")
            print(f"    Valid: {candidate.is_valid}")
            if not candidate.is_valid:
                print(f"    Error: {candidate.validation_error}")
            
            # Test the XPath manually
            try:
                elements_found = runner_page.locator(candidate.xpath).count()
                print(f"    Manual test - Elements found: {elements_found}")
                
                # Also test with a simpler XPath to see if the element exists
                tag = candidate.element.get('tag', 'div')
                simple_xpath = f"//{tag}"
                simple_count = runner_page.locator(simple_xpath).count()
                print(f"    Simple test - {tag} elements found: {simple_count}")
                
                # Test with partial text match
                text = candidate.element.get('text', '').strip()
                if text:
                    partial_xpath = f"//{tag}[contains(text(), '{text[:10]}')]"
                    partial_count = runner_page.locator(partial_xpath).count()
                    print(f"    Partial text test - Elements found: {partial_count}")
                    
            except Exception as e:
                print(f"    Manual test - Error: {e}")
        
        # Select best candidate
        best_candidate = xpath_validator.select_best_candidate(validated_candidates)
        if best_candidate:
            print(f"\n6. Best candidate selected:")
            print(f"    XPath: {best_candidate.xpath}")
            print(f"    Strategy: {best_candidate.strategy}")
            print(f"    Confidence: {best_candidate.confidence}")
        else:
            print(f"\n6. No valid candidates found")
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_xpath_generation()