"""
Verizon Flow Test Case for HER Framework

Tests the complete deterministic pipeline with real Verizon.com flow:
1. Open https://www.verizon.com/smartphones/apple/
2. Click "iPhone 16 Pro"
3. Validate "Apple iPhone 16 Pro" on detail page

This test validates the end-to-end functionality of the new deterministic
+ reranker-based pipeline.
"""

import pytest
import time
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from her.core.deterministic_pipeline import DeterministicPipeline, create_deterministic_pipeline
from her.core.runner import Runner
from her.intent.enhanced_parser import EnhancedIntentParser
from her.descriptors.canonical import CanonicalDescriptorBuilder


class TestVerizonFlow:
    """Test the Verizon iPhone 16 Pro flow using the deterministic pipeline."""
    
    @pytest.fixture
    def runner(self):
        """Create a test runner instance."""
        return Runner(headless=True)
    
    @pytest.fixture
    def pipeline(self, runner):
        """Create a deterministic pipeline instance."""
        page = runner._ensure_browser()
        return create_deterministic_pipeline(page)
    
    def test_verizon_iphone_16_pro_flow(self, runner, pipeline):
        """Test the complete Verizon iPhone 16 Pro flow."""
        print("\n🧪 Testing Verizon iPhone 16 Pro Flow")
        print("=" * 50)
        
        # Test steps
        steps = [
            "Open https://www.verizon.com/smartphones/apple/",
            'Click "iPhone 16 Pro"',
            'Validate "Apple iPhone 16 Pro"'
        ]
        
        results = []
        
        for i, step in enumerate(steps, 1):
            print(f"\n📋 Step {i}: {step}")
            print("-" * 30)
            
            try:
                # Execute step through deterministic pipeline
                result = pipeline.execute_step(step)
                
                # Log result
                print(f"✅ Success: {result.success}")
                print(f"   Selector: {result.selector}")
                print(f"   Confidence: {result.confidence:.3f}")
                print(f"   Action: {result.action}")
                print(f"   Target: {result.target}")
                print(f"   Execution Time: {result.execution_time_ms:.1f}ms")
                
                if result.stages_timing:
                    print(f"   Stage Timings:")
                    for stage, timing in result.stages_timing.items():
                        print(f"     {stage}: {timing:.1f}ms")
                
                if result.error:
                    print(f"❌ Error: {result.error}")
                    print(f"   Error Stage: {result.error_stage}")
                
                results.append(result)
                
                # Brief pause between steps
                time.sleep(1.0)
                
            except Exception as e:
                print(f"❌ Step {i} failed: {e}")
                results.append(None)
                break
        
        # Validate results
        self._validate_results(results)
        
        print(f"\n🎯 Test Summary:")
        print(f"   Total Steps: {len(steps)}")
        print(f"   Successful: {sum(1 for r in results if r and r.success)}")
        print(f"   Failed: {sum(1 for r in results if not r or not r.success)}")
        
        # Cleanup
        runner._close()
    
    def test_intent_parsing(self):
        """Test the enhanced intent parser."""
        print("\n🧪 Testing Enhanced Intent Parser")
        print("=" * 40)
        
        parser = EnhancedIntentParser()
        
        test_cases = [
            'Click "Login"',
            'Type $"John123" into "Username"',
            'Validate "Welcome back"',
            'Open https://www.verizon.com/',
            'Wait 2 seconds'
        ]
        
        for step in test_cases:
            print(f"\n📝 Parsing: {step}")
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
    
    def test_canonical_descriptor_builder(self):
        """Test the canonical descriptor builder."""
        print("\n🧪 Testing Canonical Descriptor Builder")
        print("=" * 45)
        
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
        
        print(f"📋 Canonical Node:")
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
    
    def test_target_text_matcher(self):
        """Test the target text matcher."""
        print("\n🧪 Testing Target Text Matcher")
        print("=" * 35)
        
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
    
    def test_robust_xpath_builder(self):
        """Test the robust XPath builder."""
        print("\n🧪 Testing Robust XPath Builder")
        print("=" * 38)
        
        from her.locator.robust_xpath_builder import RobustXPathBuilder
        from her.descriptors.canonical import CanonicalNode
        
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
        print(f"📋 Generated XPath: {xpath}")
        
        # Validate XPath
        is_valid, error = builder.validate_xpath(xpath)
        if is_valid:
            print(f"✅ XPath is valid")
        else:
            print(f"❌ XPath is invalid: {error}")
        
        # Test alternative XPaths
        alternatives = builder.build_alternative_xpaths(mock_node, max_alternatives=3)
        print(f"📋 Alternative XPaths ({len(alternatives)}):")
        for i, alt_xpath in enumerate(alternatives, 1):
            print(f"   {i}. {alt_xpath}")
    
    def _validate_results(self, results):
        """Validate test results."""
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"
        
        # Check that all steps succeeded
        for i, result in enumerate(results, 1):
            assert result is not None, f"Step {i} returned None"
            assert result.success, f"Step {i} failed: {result.error}"
        
        # Check specific step results
        step1 = results[0]
        assert step1.action == 'navigate', f"Step 1 action should be 'navigate', got '{step1.action}'"
        assert 'verizon.com' in step1.target, f"Step 1 target should contain 'verizon.com', got '{step1.target}'"
        
        step2 = results[1]
        assert step2.action == 'click', f"Step 2 action should be 'click', got '{step2.action}'"
        assert 'iPhone 16 Pro' in step2.target, f"Step 2 target should contain 'iPhone 16 Pro', got '{step2.target}'"
        
        step3 = results[2]
        assert step3.action == 'validate', f"Step 3 action should be 'validate', got '{step3.action}'"
        assert 'Apple iPhone 16 Pro' in step3.target, f"Step 3 target should contain 'Apple iPhone 16 Pro', got '{step3.target}'"


if __name__ == "__main__":
    # Run the test directly
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))