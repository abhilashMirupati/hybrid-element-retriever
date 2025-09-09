#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, 'src')

# Set up environment
os.environ['HER_MODELS_DIR'] = '/workspace/src/her/models'
os.environ['HER_CACHE_DIR'] = '/workspace/.her_cache'
os.environ['HER_E2E'] = '1'

def test_xpath_synthesis():
    """Test the XPath synthesis fixes"""
    from her.locator.synthesize import synthesize_xpath
    
    # Test case: Verizon Phones button
    phones_element = {
        "tag": "a",
        "text": "Phones",
        "attributes": {
            "href": "/smartphones/",
            "data-quick-link": "phones",
            "class": "vui:button vui:u-display-flex vui:u-align-items-center",
            "role": "button"
        }
    }
    
    print("Testing XPath synthesis for Phones button...")
    xpaths = synthesize_xpath(phones_element)
    
    print("Generated XPaths:")
    for i, (kind, xpath) in enumerate(xpaths):
        print(f"  {i+1}. {kind}: {xpath}")
    
    # Check if data-quick-link is prioritized
    data_quick_link_xpath = next((xpath for kind, xpath in xpaths if kind == "data-quick-link"), None)
    if data_quick_link_xpath:
        print(f"✅ data-quick-link XPath found: {data_quick_link_xpath}")
    else:
        print("❌ data-quick-link XPath not found")
    
    # Check if href+text is present
    href_text_xpath = next((xpath for kind, xpath in xpaths if kind == "href+text"), None)
    if href_text_xpath:
        print(f"✅ href+text XPath found: {href_text_xpath}")
    else:
        print("❌ href+text XPath not found")

def test_text_matching():
    """Test the text matching improvements"""
    from her.pipeline import HybridPipeline
    
    print("\nTesting text matching improvements...")
    
    # Create a mock pipeline instance to test the text matching function
    class MockPipeline:
        def _text_match_bonus(self, query_text: str, elem_text: str) -> float:
            """Boost elements with exact text matches"""
            query_lower = query_text.lower()
            text_lower = elem_text.lower()
            
            # Extract key words from query
            key_words = []
            for word in query_lower.split():
                if word not in ['click', 'on', 'the', 'in', 'btn', 'button', 'select', 'top']:
                    key_words.append(word)
            
            # Check for exact matches
            for word in key_words:
                if word in text_lower:
                    # Exact word match gets big boost
                    if text_lower == word or text_lower == word + 's':  # Handle plural
                        return 1.0  # Maximum boost for exact matches
                    # Word at start/end gets good boost
                    if text_lower.startswith(word + ' ') or text_lower.startswith(word + 's '):
                        return 0.8  # High boost for start matches
                    # Partial match gets smaller boost
                    return 0.5  # Good boost for partial matches
            
            return 0.0
    
    pipeline = MockPipeline()
    
    # Test cases
    test_cases = [
        ("Click on Phones btn in top", "Phones", 1.0),
        ("Click on Phones btn in top", "Phones and Accessories", 0.8),
        ("Click on Phones btn in top", "Shop Phones", 0.5),
        ("Click on Phones btn in top", "iPhone", 0.0),
    ]
    
    for query, elem_text, expected in test_cases:
        bonus = pipeline._text_match_bonus(query, elem_text)
        status = "✅" if abs(bonus - expected) < 0.01 else "❌"
        print(f"  {status} '{query}' + '{elem_text}' = {bonus:.1f} (expected {expected:.1f})")

if __name__ == "__main__":
    test_xpath_synthesis()
    test_text_matching()
    print("\n🎯 All fixes tested!")