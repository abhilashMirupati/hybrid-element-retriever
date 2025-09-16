#!/usr/bin/env python3
"""
Demonstration script for MarkupLM integration in HER framework.

This script demonstrates the MarkupLM-enhanced no-semantic mode with hierarchical context.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables for no-semantic mode with hierarchy
os.environ["HER_USE_SEMANTIC_SEARCH"] = "false"
os.environ["HER_USE_HIERARCHY"] = "true"
os.environ["HER_USE_MARKUPLM_NO_SEMANTIC"] = "true"
os.environ["HER_DEBUG"] = "true"

from her.locator.markuplm_no_semantic import MarkupLMNoSemanticMatcher
from her.embeddings.markuplm_snippet_scorer import MarkupLMSnippetScorer
from her.descriptors.markuplm_hierarchy_builder import MarkupLMHierarchyBuilder
from her.utils.xpath_generator import generate_xpath_candidates


def create_sample_elements():
    """Create sample HTML elements for testing."""
    return [
        # Apple filter button
        {
            "tag": "button",
            "text": "Apple",
            "attributes": {
                "id": "apple-filter-btn",
                "class": "filter-button active",
                "data-testid": "apple-filter",
                "aria-label": "Filter by Apple brand",
                "role": "button"
            },
            "visible": True,
            "xpath": "//button[@id='apple-filter-btn']"
        },
        # Samsung filter button
        {
            "tag": "button",
            "text": "Samsung",
            "attributes": {
                "id": "samsung-filter-btn",
                "class": "filter-button",
                "data-testid": "samsung-filter",
                "aria-label": "Filter by Samsung brand"
            },
            "visible": True,
            "xpath": "//button[@id='samsung-filter-btn']"
        },
        # Apple link in navigation
        {
            "tag": "a",
            "text": "Apple",
            "attributes": {
                "href": "/brands/apple",
                "class": "brand-link",
                "aria-label": "Visit Apple brand page"
            },
            "visible": True,
            "xpath": "//a[@href='/brands/apple']"
        },
        # Search input
        {
            "tag": "input",
            "text": "",
            "attributes": {
                "type": "search",
                "placeholder": "Search for products...",
                "name": "search",
                "id": "search-input"
            },
            "visible": True,
            "xpath": "//input[@id='search-input']"
        },
        # Generic div (should not match)
        {
            "tag": "div",
            "text": "Some random content",
            "attributes": {
                "class": "content"
            },
            "visible": True,
            "xpath": "//div[@class='content']"
        }
    ]


def demonstrate_markuplm_scorer():
    """Demonstrate MarkupLM snippet scorer."""
    print("🔍 MarkupLM Snippet Scorer Demonstration")
    print("=" * 50)
    
    try:
        # Create scorer (this will fail if MarkupLM is not available)
        scorer = MarkupLMSnippetScorer()
        
        if not scorer.is_available():
            print("❌ MarkupLM not available, using mock demonstration")
            return demonstrate_mock_scoring()
        
        print("✅ MarkupLM scorer initialized successfully")
        
        # Create sample candidates with hierarchical context
        candidates = [
            {
                'element': {
                    'tag': 'button',
                    'text': 'Apple',
                    'attributes': {'id': 'apple-btn', 'class': 'filter-button'}
                },
                'parents': [
                    {
                        'tag': 'div',
                        'attributes': {'class': 'filter-container'},
                        'text': 'Brand Filters'
                    }
                ],
                'siblings': [
                    {
                        'tag': 'button',
                        'text': 'Samsung',
                        'attributes': {'id': 'samsung-btn'}
                    }
                ]
            }
        ]
        
        query = 'Click on "Apple" filter'
        
        print(f"Query: {query}")
        print(f"Candidates: {len(candidates)}")
        
        # Score snippets
        results = scorer.score_snippets(candidates, query)
        
        print(f"\nScoring Results:")
        for i, result in enumerate(results):
            print(f"  {i+1}. Score: {result.score:.3f}")
            print(f"     XPath: {result.xpath}")
            print(f"     Confidence: {result.confidence:.3f}")
            print(f"     Reasons: {', '.join(result.reasons)}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ MarkupLM scorer failed: {e}")
        return demonstrate_mock_scoring()


def demonstrate_mock_scoring():
    """Demonstrate mock scoring when MarkupLM is not available."""
    print("🔍 Mock Snippet Scoring Demonstration")
    print("=" * 50)
    
    # Mock scoring results
    mock_results = [
        {
            'element': {'tag': 'button', 'text': 'Apple', 'attributes': {'id': 'apple-btn'}},
            'score': 0.95,
            'xpath': '//button[@id="apple-btn"]',
            'confidence': 0.95,
            'reasons': ['exact_text_match', 'interactive_element', 'has_id']
        },
        {
            'element': {'tag': 'a', 'text': 'Apple', 'attributes': {'href': '/apple'}},
            'score': 0.80,
            'xpath': '//a[@href="/apple"]',
            'confidence': 0.80,
            'reasons': ['exact_text_match', 'link_element']
        }
    ]
    
    print("Mock scoring results:")
    for i, result in enumerate(mock_results):
        print(f"  {i+1}. Score: {result['score']:.3f}")
        print(f"     XPath: {result['xpath']}")
        print(f"     Confidence: {result['confidence']:.3f}")
        print(f"     Reasons: {', '.join(result['reasons'])}")
        print()
    
    return True


def demonstrate_hierarchy_builder():
    """Demonstrate hierarchy builder."""
    print("🏗️  Hierarchy Builder Demonstration")
    print("=" * 50)
    
    builder = MarkupLMHierarchyBuilder()
    
    # Sample elements
    elements = create_sample_elements()
    
    # Build hierarchical context
    enhanced_candidates = builder.build_context_for_candidates(elements[:2], elements)
    
    print(f"Enhanced {len(enhanced_candidates)} candidates with hierarchical context")
    
    for i, candidate in enumerate(enhanced_candidates):
        print(f"\nCandidate {i+1}:")
        print(f"  Element: {candidate['element']['tag']} - {candidate['element']['text']}")
        print(f"  Parents: {len(candidate['parents'])}")
        print(f"  Siblings: {len(candidate['siblings'])}")
        print(f"  Depth: {candidate['depth']}")
        print(f"  Hierarchy Path: {' > '.join(candidate['hierarchy_path'])}")
        print(f"  HTML Context Length: {len(candidate['html_context'])} chars")
    
    return True


def demonstrate_xpath_generation():
    """Demonstrate XPath generation."""
    print("🎯 XPath Generation Demonstration")
    print("=" * 50)
    
    # Sample element
    element = {
        'tag': 'button',
        'text': 'Apple',
        'attributes': {
            'id': 'apple-filter-btn',
            'class': 'filter-button active',
            'data-testid': 'apple-filter',
            'aria-label': 'Filter by Apple brand'
        }
    }
    
    # Generate XPath candidates
    candidates = generate_xpath_candidates(element)
    
    print(f"Generated {len(candidates)} XPath candidates for element:")
    print(f"  Tag: {element['tag']}")
    print(f"  Text: {element['text']}")
    print(f"  Attributes: {element['attributes']}")
    print()
    
    for i, candidate in enumerate(candidates):
        print(f"  {i+1}. Strategy: {candidate.strategy}")
        print(f"     XPath: {candidate.xpath}")
        print(f"     Confidence: {candidate.confidence:.3f}")
        print()
    
    return True


def demonstrate_full_workflow():
    """Demonstrate the full MarkupLM no-semantic workflow."""
    print("🚀 Full MarkupLM No-Semantic Workflow Demonstration")
    print("=" * 60)
    
    try:
        # Create matcher
        matcher = MarkupLMNoSemanticMatcher()
        
        if not matcher.is_markup_available():
            print("⚠️  MarkupLM not available, using fallback mode")
        
        # Sample elements
        elements = create_sample_elements()
        
        # Test queries
        test_queries = [
            'Click on "Apple" filter',
            'Select the Apple brand button',
            'Find the search input field',
            'Click on Samsung filter'
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: {query}")
            print("-" * 40)
            
            result = matcher.query(query, elements)
            
            if result.get('xpath'):
                print(f"✅ Found element:")
                print(f"   XPath: {result['xpath']}")
                print(f"   Confidence: {result['confidence']:.3f}")
                print(f"   Strategy: {result['strategy']}")
                if 'reasons' in result:
                    print(f"   Reasons: {', '.join(result['reasons'])}")
            else:
                print(f"❌ No element found")
                if 'error' in result:
                    print(f"   Error: {result['error']}")
    
    except Exception as e:
        print(f"❌ Full workflow demonstration failed: {e}")
        return False
    
    return True


def main():
    """Main demonstration function."""
    print("🎉 MarkupLM Integration Demonstration")
    print("=" * 60)
    print("This demonstration shows the MarkupLM-enhanced no-semantic mode")
    print("with hierarchical context for element ranking and XPath generation.")
    print()
    
    # Run demonstrations
    demonstrations = [
        ("MarkupLM Snippet Scorer", demonstrate_markuplm_scorer),
        ("Hierarchy Builder", demonstrate_hierarchy_builder),
        ("XPath Generation", demonstrate_xpath_generation),
        ("Full Workflow", demonstrate_full_workflow)
    ]
    
    results = []
    
    for name, demo_func in demonstrations:
        print(f"\n{'='*60}")
        print(f"Running: {name}")
        print('='*60)
        
        try:
            success = demo_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            results.append((name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("DEMONSTRATION SUMMARY")
    print('='*60)
    
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\nOverall: {passed}/{total} demonstrations passed")
    
    if passed == total:
        print("🎉 All demonstrations completed successfully!")
    else:
        print("⚠️  Some demonstrations failed. Check the output above for details.")


if __name__ == "__main__":
    main()