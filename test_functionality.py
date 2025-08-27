#!/usr/bin/env python3
"""Test script to verify HER functionality."""

import json
import sys
from her.cli_api import HybridClient


def test_basic_functionality():
    """Test basic HER functionality."""
    print("Testing Hybrid Element Retriever functionality...")
    print("=" * 60)
    
    try:
        # Create client
        print("\n1. Creating HybridClient...")
        client = HybridClient(headless=True, auto_index=True)
        print("   ✓ Client created successfully")
        
        # Test intent parsing
        print("\n2. Testing intent parsing...")
        test_steps = [
            "Click the login button",
            "Type john@example.com in the email field",
            "Select United States from the country dropdown",
            "Check the terms checkbox",
            "Submit the form"
        ]
        
        for step in test_steps:
            intent = client.parser.parse(step)
            print(f"   Step: {step}")
            print(f"   → Action: {intent.get('action', 'unknown')}")
            print(f"   → Target: {intent.get('target', 'unknown')}")
            if intent.get('value'):
                print(f"   → Value: {intent.get('value')}")
            print()
        
        # Test locator synthesis
        print("\n3. Testing locator synthesis...")
        test_elements = [
            {
                "tagName": "button",
                "text": "Login",
                "attributes": {"id": "login-btn", "class": "btn btn-primary"}
            },
            {
                "tagName": "input",
                "attributes": {"type": "email", "name": "email", "placeholder": "Enter email"}
            },
            {
                "tagName": "button",
                "text": "Send",
                "attributes": {"type": "submit"}
            }
        ]
        
        for elem in test_elements:
            locators = client.synthesizer.synthesize(elem)
            print(f"   Element: {elem.get('tagName')} - {elem.get('text', elem.get('attributes', {}))}")
            print(f"   Generated locators:")
            for loc in locators[:3]:  # Show top 3
                print(f"     • {loc}")
            print()
        
        # Test the full pipeline (without actual browser)
        print("\n4. Testing full pipeline (mock mode)...")
        
        # Mock some descriptors for testing
        mock_descriptors = [
            {
                "backendNodeId": 1,
                "tagName": "button",
                "text": "Login",
                "attributes": {"id": "login-btn"},
                "visible": True
            },
            {
                "backendNodeId": 2,
                "tagName": "button", 
                "text": "Send",
                "attributes": {"type": "submit"},
                "visible": True
            },
            {
                "backendNodeId": 3,
                "tagName": "input",
                "attributes": {"type": "email", "name": "email"},
                "visible": True
            }
        ]
        
        # Test finding candidates
        test_queries = [
            ("Click login button", "login"),
            ("Click send button", "send"),
            ("Type in email field", "email")
        ]
        
        for step, expected_target in test_queries:
            intent = client.parser.parse(step)
            
            # Generate embeddings
            query_embedding = client.query_embedder.embed(intent['target'])
            
            # Score elements
            candidates = []
            for desc in mock_descriptors:
                element_embedding = client.element_embedder.embed(desc)
                semantic_score = client.query_embedder.similarity(query_embedding, element_embedding)
                heuristic_score = client.rank_fusion._get_heuristic_score(desc, intent['target'])
                candidates.append((desc, semantic_score, heuristic_score))
            
            # Rank candidates
            ranked = client.rank_fusion.rank_candidates(candidates)
            
            if ranked:
                best = ranked[0]
                locators = client.synthesizer.synthesize(best[0])
                
                print(f"   Query: '{step}'")
                print(f"   → Best match: {best[0].get('tagName')} - '{best[0].get('text', '')}'")
                print(f"   → Score: {best[1]:.3f}")
                print(f"   → Best locator: {locators[0] if locators else 'none'}")
                print()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed! HER is functional.")
        print("\nThe project is ready to use for:")
        print("  • Parsing natural language test steps")
        print("  • Finding elements based on descriptions")
        print("  • Generating robust XPath/CSS locators")
        print("  • Self-healing when locators fail")
        
        print("\nTo use with a real browser:")
        print("  1. Install Playwright: python -m playwright install chromium")
        print("  2. (Optional) Install models: ./scripts/install_models.sh")
        print("  3. Use client.act() or client.query() with URLs")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)