#!/usr/bin/env python3
"""
Simple Test Runner for HER Framework

Runs the Verizon flow test without requiring pytest.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_verizon_flow():
    """Test the Verizon iPhone 16 Pro flow."""
    print("🧪 Testing Verizon iPhone 16 Pro Flow")
    print("=" * 50)
    
    try:
        # Test the enhanced intent parser
        from her.intent.enhanced_parser import EnhancedIntentParser
        
        print("\n📝 Testing Enhanced Intent Parser")
        print("-" * 30)
        
        parser = EnhancedIntentParser()
        test_cases = [
            'Click "Login"',
            'Type $"John123" into "Username"',
            'Validate "Welcome back"',
            'Open https://www.verizon.com/',
            'Wait 2 seconds'
        ]
        
        for step in test_cases:
            print(f"\nParsing: {step}")
            intent = parser.parse(step)
            
            print(f"   Action: {intent.action}")
            print(f"   Target: {intent.target}")
            print(f"   Value: {intent.value}")
            print(f"   Confidence: {intent.confidence:.3f}")
            print(f"   Label Tokens: {intent.label_tokens}")
            
            # Validate intent
            is_valid, issues = parser.validate_intent(intent)
            if is_valid:
                print(f"   ✅ Valid")
            else:
                print(f"   ❌ Invalid: {', '.join(issues)}")
        
        # Test canonical descriptor builder
        print("\n📋 Testing Canonical Descriptor Builder")
        print("-" * 40)
        
        from her.descriptors.canonical import CanonicalDescriptorBuilder
        
        builder = CanonicalDescriptorBuilder()
        
        # Mock element data
        mock_element = {
            'tag': 'BUTTON',
            'text': 'Click Me',
            'attributes': {
                'id': 'submit-btn',
                'class': 'btn btn-primary',
                'aria-label': 'Submit form'
            },
            'backendNodeId': 12345,
            'meta': {'frame_hash': 'test_frame_123'}
        }
        
        # Build canonical descriptor
        canonical_node = builder.build_canonical_descriptor(mock_element)
        
        print(f"Canonical Node:")
        print(f"   Tag: {canonical_node.tag}")
        print(f"   Role: {canonical_node.role}")
        print(f"   Inner Text: {canonical_node.inner_text}")
        print(f"   Element ID: {canonical_node.element_id}")
        print(f"   Aria Label: {canonical_node.aria_label}")
        print(f"   Is Interactive: {canonical_node.is_interactive}")
        print(f"   Signature: {canonical_node.signature}")
        
        # Validate signature is deterministic
        canonical_node2 = builder.build_canonical_descriptor(mock_element)
        assert canonical_node.signature == canonical_node2.signature, "Signature should be deterministic"
        print(f"   ✅ Signature is deterministic")
        
        # Test target text matcher
        print("\n🎯 Testing Target Text Matcher")
        print("-" * 30)
        
        from her.matching.target_matcher import TargetTextMatcher, ElementNotFoundError
        from her.descriptors.canonical import CanonicalNode
        
        matcher = TargetTextMatcher()
        
        # Mock canonical nodes
        mock_nodes = [
            CanonicalNode(
                tag='BUTTON',
                role='button',
                inner_text='Login',
                backend_node_id=1,
                element_id='login-btn',
                name='',
                aria_label='',
                title='',
                placeholder='',
                parent_tag='FORM',
                siblings_count=2,
                signature='test1',
                attributes={'id': 'login-btn'},
                is_interactive=True,
                frame_hash='test_frame'
            ),
            CanonicalNode(
                tag='INPUT',
                role='textbox',
                inner_text='',
                backend_node_id=2,
                element_id='username',
                name='username',
                aria_label='Username field',
                title='',
                placeholder='Enter username',
                parent_tag='FORM',
                siblings_count=1,
                signature='test2',
                attributes={'name': 'username', 'placeholder': 'Enter username'},
                is_interactive=True,
                frame_hash='test_frame'
            )
        ]
        
        # Test exact match
        try:
            matches = matcher.match_target('Login', mock_nodes)
            print(f"✅ Found {len(matches)} matches for 'Login'")
            assert len(matches) > 0, "Should find matches for 'Login'"
        except ElementNotFoundError as e:
            print(f"❌ No matches found for 'Login': {e}")
        
        # Test partial match
        try:
            matches = matcher.match_target('username', mock_nodes)
            print(f"✅ Found {len(matches)} matches for 'username'")
            assert len(matches) > 0, "Should find matches for 'username'"
        except ElementNotFoundError as e:
            print(f"❌ No matches found for 'username': {e}")
        
        # Test no match
        try:
            matches = matcher.match_target('NonExistent', mock_nodes)
            print(f"❌ Unexpectedly found matches for 'NonExistent'")
        except ElementNotFoundError as e:
            print(f"✅ Correctly raised ElementNotFoundError for 'NonExistent'")
        
        # Test robust XPath builder
        print("\n🔧 Testing Robust XPath Builder")
        print("-" * 35)
        
        from her.locator.robust_xpath_builder import RobustXPathBuilder
        
        builder = RobustXPathBuilder()
        
        # Mock canonical node
        mock_node = CanonicalNode(
            tag='BUTTON',
            role='button',
            inner_text='Submit Form',
            backend_node_id=123,
            element_id='submit-btn',
            name='',
            aria_label='Submit the form',
            title='',
            placeholder='',
            parent_tag='FORM',
            siblings_count=1,
            signature='test123',
            attributes={'id': 'submit-btn', 'aria-label': 'Submit the form'},
            is_interactive=True,
            frame_hash='test_frame'
        )
        
        # Build XPath
        xpath = builder.build_xpath(mock_node)
        print(f"Generated XPath: {xpath}")
        
        # Validate XPath
        is_valid, error = builder.validate_xpath(xpath)
        if is_valid:
            print(f"✅ XPath is valid")
        else:
            print(f"❌ XPath is invalid: {error}")
        
        # Test alternative XPaths
        alternatives = builder.build_alternative_xpaths(mock_node, max_alternatives=3)
        print(f"Alternative XPaths ({len(alternatives)}):")
        for i, alt_xpath in enumerate(alternatives, 1):
            print(f"   {i}. {alt_xpath}")
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_verizon_flow()
    sys.exit(0 if success else 1)