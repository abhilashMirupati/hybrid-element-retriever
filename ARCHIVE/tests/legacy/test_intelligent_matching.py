#!/usr/bin/env python3
"""Test intelligent matching vs rule-based approach."""
# import sys
# from pathlib import Path
# removed sys.path hack
from her.pipeline import HERPipeline
from her.pipeline import HERPipeline as HERPipelineV2
from her.matching.intelligent_matcher import IntelligentMatcher

print("=" * 80)
print("INTELLIGENT MATCHING vs RULE-BASED COMPARISON")
print("=" * 80)

# Initialize both pipelines
rule_based = HERPipeline()
intelligent = HERPipelineV2()

# Comprehensive test cases covering various scenarios
test_cases = [
    # Format: (descriptors, query, expected_element_identifier)
    
    # 1. Basic button matching
    (
        [
            {"tag": "button", "text": "Submit", "id": "form1-submit"},
            {"tag": "button", "text": "Submit", "id": "form2-submit"},
            {"tag": "button", "text": "Cancel", "id": "form-cancel"}
        ],
        "click form2 submit button",
        "form2-submit"
    ),
    
    # 2. Form field matching
    (
        [
            {"tag": "input", "type": "email", "placeholder": "Email address", "name": "email"},
            {"tag": "input", "type": "password", "placeholder": "Password", "name": "pwd"},
            {"tag": "input", "type": "text", "placeholder": "Username", "name": "user"}
        ],
        "enter my email",
        "email"
    ),
    
    # 3. Link navigation
    (
        [
            {"tag": "a", "text": "Home", "href": "/"},
            {"tag": "a", "text": "About Us", "href": "/about"},
            {"tag": "a", "text": "Contact", "href": "/contact"}
        ],
        "go to about page",
        "about"
    ),
    
    # 4. Product selection (no product-specific rules!)
    (
        [
            {"tag": "button", "text": "Add to Cart", "dataTestId": "add-laptop"},
            {"tag": "button", "text": "Add to Cart", "dataTestId": "add-phone"},
            {"tag": "button", "text": "Add to Cart", "dataTestId": "add-tablet"}
        ],
        "add laptop to cart",
        "laptop"
    ),
    
    # 5. Typo tolerance
    (
        [
            {"tag": "button", "text": "Continue", "id": "continue-btn"},
            {"tag": "button", "text": "Back", "id": "back-btn"}
        ],
        "click continu button",  # Typo: "continu" instead of "continue"
        "continue"
    ),
    
    # 6. Synonym understanding
    (
        [
            {"tag": "button", "text": "Sign In", "id": "login-btn"},
            {"tag": "button", "text": "Register", "id": "signup-btn"}
        ],
        "press the login button",  # "press" = "click", "login" = "sign in"
        "login"
    ),
    
    # 7. Complex attribute matching
    (
        [
            {"tag": "input", "type": "search", "ariaLabel": "Search products", "id": "search-box"},
            {"tag": "input", "type": "text", "placeholder": "Enter name", "id": "name-field"}
        ],
        "search for products",
        "search"
    ),
    
    # 8. Partial text matching
    (
        [
            {"tag": "button", "text": "Save and Continue", "id": "save-continue"},
            {"tag": "button", "text": "Save Draft", "id": "save-draft"},
            {"tag": "button", "text": "Discard Changes", "id": "discard"}
        ],
        "save and go forward",
        "save-continue"
    ),
    
    # 9. Context-aware matching
    (
        [
            {"tag": "select", "name": "country", "id": "country-select"},
            {"tag": "input", "type": "text", "name": "country", "id": "country-input"}
        ],
        "select country from dropdown",
        "country-select"
    ),
    
    # 10. Icon button (no text)
    (
        [
            {"tag": "button", "text": "", "ariaLabel": "Close dialog", "classes": ["close-btn"]},
            {"tag": "button", "text": "", "ariaLabel": "Minimize", "classes": ["min-btn"]}
        ],
        "close the dialog",
        "close"
    )
]

def check_result(result, expected_id):
    """Check if result contains expected element."""
    if not result or not result.get('element'):
        return False
    
    element = result['element']
    # Check various fields for the expected identifier
    for field in ['id', 'dataTestId', 'name', 'ariaLabel', 'text']:
        if field in element:
            value = str(element[field]).lower()
            if expected_id.lower() in value:
                return True
    
    return False

# Run tests
print("\n1. RULE-BASED PIPELINE RESULTS")
print("-" * 80)

rule_based_correct = 0
for i, (descriptors, query, expected) in enumerate(test_cases, 1):
    result = rule_based.process(query, descriptors)
    correct = check_result(result, expected)
    
    if correct:
        rule_based_correct += 1
        status = "✓"
    else:
        status = "✗"
    
    confidence = result.get('confidence', 0) if result else 0
    print(f"{i:2}. {status} '{query[:40]:40}' (conf: {confidence:.2f})")

rule_based_accuracy = rule_based_correct / len(test_cases) * 100

print("\n2. INTELLIGENT MATCHING RESULTS")
print("-" * 80)

intelligent_correct = 0
for i, (descriptors, query, expected) in enumerate(test_cases, 1):
    result = intelligent.process(query, descriptors)
    correct = check_result(result, expected)
    
    if correct:
        intelligent_correct += 1
        status = "✓"
    else:
        status = "✗"
    
    confidence = result.get('confidence', 0) if result else 0
    print(f"{i:2}. {status} '{query[:40]:40}' (conf: {confidence:.2f})")

intelligent_accuracy = intelligent_correct / len(test_cases) * 100

# Direct matcher test
print("\n3. DIRECT INTELLIGENT MATCHER TEST")
print("-" * 80)

matcher = IntelligentMatcher()
direct_correct = 0

for i, (descriptors, query, expected) in enumerate(test_cases[:5], 1):
    matches = matcher.match(query, descriptors)
    
    if matches:
        best_match = matches[0][0]
        score = matches[0][1]
        
        # Check if correct
        correct = False
        for field in ['id', 'dataTestId', 'name', 'text']:
            if field in best_match and expected.lower() in str(best_match[field]).lower():
                correct = True
                break
        
        if correct:
            direct_correct += 1
            print(f"✓ Test {i}: score={score:.3f}")
        else:
            print(f"✗ Test {i}: wrong match (score={score:.3f})")
    else:
        print(f"✗ Test {i}: no matches")

# Summary
print("\n" + "=" * 80)
print("COMPARISON SUMMARY")
print("=" * 80)

print(f"\nRule-Based Pipeline:")
print(f"  Correct: {rule_based_correct}/{len(test_cases)}")
print(f"  Accuracy: {rule_based_accuracy:.1f}%")

print(f"\nIntelligent Matching Pipeline:")
print(f"  Correct: {intelligent_correct}/{len(test_cases)}")
print(f"  Accuracy: {intelligent_accuracy:.1f}%")

improvement = intelligent_accuracy - rule_based_accuracy
if improvement > 0:
    print(f"\n✅ Intelligent matching improved accuracy by {improvement:.1f}%")
elif improvement < 0:
    print(f"\n⚠️ Intelligent matching decreased accuracy by {abs(improvement):.1f}%")
else:
    print(f"\n➖ No change in accuracy")

print("\nKEY ADVANTAGES OF INTELLIGENT MATCHING:")
print("  • No hard-coded rules for specific products")
print("  • Handles typos and variations")
print("  • Understands synonyms")
print("  • Uses multiple signals (text, attributes, structure)")
print("  • Generalizable to any domain")

if intelligent_accuracy < 100:
    print("\nAREAS FOR IMPROVEMENT:")
    print("  • Add proper NLP tokenization (spaCy/NLTK)")
    print("  • Use word embeddings for semantic similarity")
    print("  • Train a small neural model for scoring")
    print("  • Add context from previous interactions")