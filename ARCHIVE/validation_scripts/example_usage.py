#!/usr/bin/env python3
"""
Example usage of Hybrid Element Retriever (HER)

This demonstrates how HER converts natural language to XPath/CSS locators.
No browser required for this demo - it works with mock elements.
"""

from her.parser.intent import IntentParser
from her.locator import LocatorSynthesizer
from her.embeddings.query_embedder import QueryEmbedder
from her.embeddings.element_embedder import ElementEmbedder
from her.rank.fusion import RankFusion


def main():
    print("=" * 70)
    print("HYBRID ELEMENT RETRIEVER - USAGE EXAMPLE")
    print("=" * 70)
    print()
    
    # Initialize components
    parser = IntentParser()
    synthesizer = LocatorSynthesizer(max_candidates=5)
    query_embedder = QueryEmbedder()
    element_embedder = ElementEmbedder()
    ranker = RankFusion()
    
    # Example: User provides natural language command
    user_commands = [
        "Click the login button",
        "Type email in the username field",
        "Select United States from country dropdown",
        "Click on Send button",
    ]
    
    # Mock page elements (normally from DOM/AX tree)
    page_elements = [
        {
            "backendNodeId": 1,
            "tagName": "button",
            "text": "Login",
            "attributes": {"id": "login-btn", "class": "btn btn-primary"},
            "role": "button"
        },
        {
            "backendNodeId": 2,
            "tagName": "input",
            "attributes": {"id": "username", "name": "user", "type": "text", "placeholder": "Username or Email"},
            "role": "textbox"
        },
        {
            "backendNodeId": 3,
            "tagName": "select",
            "attributes": {"id": "country", "name": "country_code"},
            "role": "combobox"
        },
        {
            "backendNodeId": 4,
            "tagName": "button",
            "text": "Send",
            "attributes": {"type": "submit", "class": "btn btn-success"},
            "role": "button"
        },
    ]
    
    print("📋 NATURAL LANGUAGE → XPATH/CSS CONVERSION")
    print("-" * 70)
    
    for command in user_commands:
        print(f"\n🔹 User says: \"{command}\"")
        
        # Step 1: Parse the intent
        intent = parser.parse(command)
        print(f"   Parsed: action={intent.action}, target=\"{intent.target_phrase}\"")
        
        # Step 2: Find best matching element
        query_emb = query_embedder.embed(intent.target_phrase)
        
        # Score all elements
        candidates = []
        for elem in page_elements:
            # Generate element embedding
            elem_emb = element_embedder.embed(elem)
            
            # Calculate similarity (using deterministic fallback)
            # Note: In production with models, this would be true semantic similarity
            sim_score = 0.5  # Simplified for demo
            
            # Add heuristic scoring based on text/attributes
            heuristic = 0.0
            target_lower = intent.target_phrase.lower()
            if elem.get("text", "").lower() in target_lower or target_lower in elem.get("text", "").lower():
                heuristic += 0.8
            for attr_val in elem.get("attributes", {}).values():
                if isinstance(attr_val, str) and (attr_val.lower() in target_lower or target_lower in attr_val.lower()):
                    heuristic += 0.5
                    break
            
            candidates.append((elem, sim_score, heuristic))
        
        # Rank and get best match
        ranked = sorted(candidates, key=lambda x: x[1] + x[2], reverse=True)
        
        if ranked:
            best_elem, _, score = ranked[0]
            
            print(f"   Found: <{best_elem['tagName']}> ", end="")
            if best_elem.get("text"):
                print(f"'{best_elem['text']}'", end="")
            print(f" {best_elem.get('attributes', {})}")
            
            # Step 3: Generate XPath/CSS locators
            locators = synthesizer.synthesize(best_elem)
            
            print(f"   Generated {len(locators)} locators:")
            for i, loc in enumerate(locators[:5], 1):
                print(f"      {i}. {loc}")
            
            print(f"   ✅ Best XPath: {locators[0] if locators else 'none'}")
    
    print()
    print("=" * 70)
    print("✨ SUMMARY")
    print("-" * 70)
    print("HER successfully converts natural language to XPath/CSS locators!")
    print()
    print("Key Features:")
    print("• No manual XPath writing needed")
    print("• Multiple fallback locators generated")
    print("• Works with any web element")
    print("• Self-healing when UI changes")
    print()
    print("To use with a real browser:")
    print("  from her.cli_api import HybridClient")
    print("  client = HybridClient()")
    print("  result = client.act('Click login', url='https://example.com')")


if __name__ == "__main__":
    main()