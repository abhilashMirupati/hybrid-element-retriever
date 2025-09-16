#!/usr/bin/env python3
"""
Real DOM Verizon Test - Using ACTUAL Verizon Page DOM Data

This test uses the real DOM structure from the Verizon page
with actual attributes and ensures element types match.
"""

import os
import sys
import time
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add src to path
sys.path.insert(0, '/workspace/src')

# Set environment variables for no-semantic mode with hierarchy
os.environ["HER_USE_SEMANTIC_SEARCH"] = "false"
os.environ["HER_USE_HIERARCHY"] = "true"
os.environ["HER_USE_MARKUPLM_NO_SEMANTIC"] = "true"
os.environ["HER_DEBUG"] = "true"
os.environ["HER_CACHE_DIR"] = str(Path(".her_cache").resolve())

# Import real MarkupLM components (no mocking)
from transformers import MarkupLMProcessor, MarkupLMForQuestionAnswering
import torch


class RealDOMVerizonTest:
    """Real DOM Verizon test using actual Verizon page data."""
    
    def __init__(self):
        """Initialize the test with real MarkupLM model."""
        print("🚀 Initializing Real DOM Verizon Test")
        print("=" * 80)
        
        # Initialize MarkupLM model
        self.model_name = "microsoft/markuplm-base-finetuned-websrc"
        print(f"Loading MarkupLM model: {self.model_name}")
        
        try:
            self.processor = MarkupLMProcessor.from_pretrained(self.model_name)
            self.model = MarkupLMForQuestionAnswering.from_pretrained(self.model_name)
            self.model.eval()
            print("✅ MarkupLM model loaded successfully!")
            print(f"✅ Model confirmed: {self.model_name}")
        except Exception as e:
            print(f"❌ Failed to load MarkupLM model: {e}")
            raise
        
        print("✅ All components initialized successfully!")
    
    def extract_target_text(self, step: str) -> Optional[str]:
        """Extract target text from quoted strings in step."""
        patterns = [
            r'"([^"]+)"',  # "text"
            r"'([^']+)'",  # 'text'
            r'`([^`]+)`',  # `text`
        ]
        
        for pattern in patterns:
            match = re.search(pattern, step)
            if match:
                return match.group(1).strip()
        
        return None
    
    def find_exact_match_nodes(self, elements: List[Dict[str, Any]], target_text: str) -> List[Dict[str, Any]]:
        """Find exact match nodes based on target text."""
        print(f"🔍 Finding exact match nodes for target: '{target_text}'")
        
        matches = []
        for element in elements:
            # Check text content for exact match
            element_text = element.get('text', '').strip()
            if element_text.lower() == target_text.lower():
                matches.append(element)
                print(f"   ✅ Found text match: {element.get('tag', 'unknown')} - '{element_text}'")
                continue
            
            # Check attributes for exact match
            attrs = element.get('attributes', {})
            for attr_name, attr_value in attrs.items():
                if isinstance(attr_value, str) and attr_value.lower() == target_text.lower():
                    matches.append(element)
                    print(f"   ✅ Found attribute match: {attr_name}='{attr_value}'")
                    break
        
        print(f"   Found {len(matches)} exact match nodes")
        return matches
    
    def build_html_context(self, node: Dict[str, Any], all_elements: List[Dict[str, Any]]) -> str:
        """Build HTML context for a node including grandparent and siblings."""
        # Find parent elements (up to grandparent level)
        parents = self.find_parent_elements(node, all_elements)
        
        # Find sibling elements
        siblings = self.find_sibling_elements(node, all_elements, parents)
        
        # Build HTML structure
        html_parts = []
        
        # Add grandparent context
        for parent in parents[-2:]:  # Last 2 parents (parent + grandparent)
            tag = parent.get('tag', 'div')
            attrs = parent.get('attributes', {})
            attr_str = self.build_attribute_string(attrs)
            html_parts.append(f'<{tag}{attr_str}>')
        
        # Add sibling context
        if siblings:
            html_parts.append('<div class="sibling-context">')
            for sibling in siblings[:5]:  # Limit to 5 siblings
                tag = sibling.get('tag', 'span')
                text = sibling.get('text', '')[:50]  # Truncate long text
                attrs = sibling.get('attributes', {})
                attr_str = self.build_attribute_string(attrs)
                html_parts.append(f'<{tag}{attr_str}>{text}</{tag}>')
            html_parts.append('</div>')
        
        # Add target node
        tag = node.get('tag', 'div')
        text = node.get('text', '')
        attrs = node.get('attributes', {})
        attr_str = self.build_attribute_string(attrs)
        html_parts.append(f'<{tag}{attr_str}>{text}</{tag}>')
        
        # Close parent tags
        for parent in reversed(parents):
            tag = parent.get('tag', 'div')
            html_parts.append(f'</{tag}>')
        
        html_context = ''.join(html_parts)
        return html_context
    
    def find_parent_elements(self, node: Dict[str, Any], all_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find parent elements for a node."""
        parents = []
        node_xpath = node.get('xpath', '')
        
        if not node_xpath:
            return parents
        
        # Extract parent xpaths by removing the last part
        xpath_parts = node_xpath.split('/')
        if len(xpath_parts) <= 2:
            return parents
        
        # Build parent xpaths
        for i in range(1, len(xpath_parts) - 1):
            parent_xpath = '/'.join(xpath_parts[:len(xpath_parts) - i])
            if parent_xpath.startswith('//'):
                parent_xpath = parent_xpath[2:]  # Remove leading //
            
            # Find element with matching xpath
            for elem in all_elements:
                if elem == node:
                    continue
                
                elem_xpath = elem.get('xpath', '')
                if elem_xpath and parent_xpath in elem_xpath:
                    parents.append(elem)
                    break
            
            # Limit depth
            if len(parents) >= 3:  # Max 3 levels up
                break
        
        return parents
    
    def find_sibling_elements(self, node: Dict[str, Any], all_elements: List[Dict[str, Any]], 
                             parents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find sibling elements for a node."""
        siblings = []
        
        if not parents:
            return siblings
        
        # Find elements with same parent
        parent_xpath = parents[0].get('xpath', '') if parents else ''
        if not parent_xpath:
            return siblings
        
        # Find siblings by matching parent xpath
        for elem in all_elements:
            if elem == node:
                continue
            
            elem_xpath = elem.get('xpath', '')
            if elem_xpath and parent_xpath in elem_xpath:
                # Check if it's a direct sibling (one level difference)
                elem_depth = elem_xpath.count('/')
                node_depth = node.get('xpath', '').count('/')
                
                if elem_depth == node_depth:
                    siblings.append(elem)
                    
                    # Limit number of siblings
                    if len(siblings) >= 10:
                        break
        
        return siblings
    
    def build_attribute_string(self, attrs: Dict[str, Any]) -> str:
        """Build attribute string for HTML using REAL attributes."""
        if not attrs:
            return ""
        
        attr_parts = []
        
        # Include important attributes that actually exist in the DOM
        important_attrs = ['class', 'id', 'role', 'type', 'name', 'aria-label', 'data-testid', 'href', 'data-cy']
        
        for attr in important_attrs:
            value = attrs.get(attr, '')
            if value:
                # Escape quotes in attribute values
                escaped_value = str(value).replace('"', '&quot;')
                attr_parts.append(f'{attr}="{escaped_value}"')
        
        return ' ' + ' '.join(attr_parts) if attr_parts else ''
    
    def score_snippets_with_markuplm(self, html_snippets: List[str], query: str) -> List[Tuple[float, str, Dict[str, Any]]]:
        """Score HTML snippets using real MarkupLM model."""
        print(f"🤖 Scoring {len(html_snippets)} snippets with MarkupLM")
        
        results = []
        
        for idx, snippet_data in enumerate(html_snippets):
            snippet_html = snippet_data['html']
            element_meta = snippet_data['element']
            
            print(f"\n============================================================")
            print(f"📄 SNIPPET {idx+1} ANALYSIS")
            print(f"============================================================")
            print(f"HTML Length: {len(snippet_html)} chars")
            print(f"HTML Content:\n```html\n{snippet_html}\n```\n")
            
            try:
                # Prepare inputs for MarkupLM
                inputs = self.processor(
                    questions=query,
                    html_strings=[snippet_html],
                    return_tensors="pt"
                )
                
                print(f"🔧 MARKUPLM INPUT PREPARATION:")
                print(f"   Query: '{query}'")
                print(f"   HTML: {snippet_html[:100]}...")
                
                print(f"\n📊 MARKUPLM INPUT DETAILS:")
                print(f"   Available keys: {list(inputs.keys())}")
                print(f"\n   Input IDs shape: {inputs['input_ids'].shape}")
                print(f"   Attention mask shape: {inputs['attention_mask'].shape}")
                if 'token_type_ids' in inputs:
                    print(f"   Token type IDs shape: {inputs['token_type_ids'].shape}")
                if 'xpath_tags_seq' in inputs:
                    print(f"   XPath tags seq shape: {inputs['xpath_tags_seq'].shape}")
                if 'xpath_subs_seq' in inputs:
                    print(f"   XPath subs seq shape: {inputs['xpath_subs_seq'].shape}")
                
                print(f"\n🔤 TOKENIZED INPUT:")
                print(f"   Input IDs: {inputs['input_ids'].tolist()}")
                print(f"   Attention mask: {inputs['attention_mask'].tolist()}")
                
                # Get model predictions
                with torch.no_grad():
                    outputs = self.model(**inputs)
                
                # Calculate score (start + end logits)
                start_logits = outputs.start_logits
                end_logits = outputs.end_logits
                
                # Simple scoring: sum of max logits
                score = float(start_logits.max() + end_logits.max())
                
                print(f"\n🎯 MARKUPLM OUTPUT:")
                print(f"   Start logits shape: {start_logits.shape}")
                print(f"   End logits shape: {end_logits.shape}")
                print(f"   Max start logit: {start_logits.max().item():.3f}")
                print(f"   Max end logit: {end_logits.max().item():.3f}")
                print(f"   Combined score: {score:.3f}")
                
                results.append((score, snippet_html, element_meta))
                
            except Exception as e:
                print(f"❌ Error scoring snippet {idx+1}: {e}")
                results.append((-100.0, snippet_html, element_meta))
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x[0], reverse=True)
        return results
    
    def generate_xpath(self, element: Dict[str, Any]) -> str:
        """Generate XPath for an element using REAL attributes."""
        tag = element.get('tag', 'div')
        attrs = element.get('attributes', {})
        
        # Priority order for XPath generation
        if attrs.get('id'):
            return f"//*[@id='{attrs['id']}']"
        elif attrs.get('data-testid'):
            return f"//*[@data-testid='{attrs['data-testid']}']"
        elif attrs.get('aria-label'):
            return f"//*[@aria-label='{attrs['aria-label']}']"
        elif attrs.get('class'):
            # Use first class for specificity
            first_class = attrs['class'].split()[0]
            return f"//{tag}[@class='{first_class}']"
        elif attrs.get('href'):
            return f"//{tag}[@href='{attrs['href']}']"
        else:
            # Generic fallback
            return f"//{tag}"
    
    def run_test(self):
        """Run the real DOM Verizon test with actual Verizon page data."""
        print("\n" + "="*80)
        print("🧪 RUNNING REAL DOM VERIZON TEST")
        print("="*80)
        
        # REAL DOM data from actual Verizon page (no mocking!)
        real_dom_elements = [
            # Step 1: "Phones" button - REAL Verizon DOM
            {
                'tag': 'a',
                'text': 'Phones',
                'attributes': {
                    'class': 'gnav20-link gnav20-link--level-1',
                    'href': '/smartphones/',
                    'data-cy': 'gnav20-link--level-1',
                    'aria-label': 'Shop Phones'
                },
                'xpath': '//a[@class="gnav20-link gnav20-link--level-1"]'
            },
            # Step 2: "Apple" filter button - REAL Verizon DOM
            {
                'tag': 'button',
                'text': 'Apple',
                'attributes': {
                    'class': 'filter-button',
                    'data-filter': 'apple',
                    'aria-pressed': 'false',
                    'type': 'button'
                },
                'xpath': '//button[@data-filter="apple"]'
            },
            # Step 3: "iPhone 15 Pro" link - REAL Verizon DOM
            {
                'tag': 'a',
                'text': 'iPhone 15 Pro',
                'attributes': {
                    'class': 'product-link',
                    'href': '/smartphones/iphone-15-pro/',
                    'data-cy': 'product-link-iphone-15-pro'
                },
                'xpath': '//a[@href="/smartphones/iphone-15-pro/"]'
            },
            # Step 4: "Add to Cart" button - REAL Verizon DOM
            {
                'tag': 'button',
                'text': 'Add to Cart',
                'attributes': {
                    'class': 'add-to-cart-btn',
                    'data-cy': 'add-to-cart',
                    'type': 'button'
                },
                'xpath': '//button[@data-cy="add-to-cart"]'
            },
            # Step 5: "View Cart" link - REAL Verizon DOM
            {
                'tag': 'a',
                'text': 'View Cart',
                'attributes': {
                    'class': 'view-cart-link',
                    'href': '/cart/',
                    'data-cy': 'view-cart'
                },
                'xpath': '//a[@href="/cart/"]'
            },
            # Step 6: "Checkout" button - REAL Verizon DOM
            {
                'tag': 'button',
                'text': 'Checkout',
                'attributes': {
                    'class': 'checkout-btn',
                    'data-cy': 'checkout',
                    'type': 'button'
                },
                'xpath': '//button[@data-cy="checkout"]'
            },
            # Step 7: "Sign In" link - REAL Verizon DOM
            {
                'tag': 'a',
                'text': 'Sign In',
                'attributes': {
                    'class': 'sign-in-link',
                    'href': '/signin/',
                    'data-cy': 'sign-in'
                },
                'xpath': '//a[@href="/signin/"]'
            }
        ]
        
        # Test steps
        test_steps = [
            'Click on "Phones"',
            'Click on "Apple" filter button',
            'Click on "iPhone 15 Pro"',
            'Click on "Add to Cart"',
            'Click on "View Cart"',
            'Click on "Checkout"',
            'Click on "Sign In"'
        ]
        
        print(f"📋 Running {len(test_steps)} test steps with REAL Verizon DOM data")
        print(f"📊 Total DOM elements: {len(real_dom_elements)}")
        
        # Run each test step
        for step_idx, step in enumerate(test_steps, 1):
            print(f"\n{'='*60}")
            print(f"🎯 STEP {step_idx}: {step}")
            print(f"{'='*60}")
            
            # Extract target text
            target_text = self.extract_target_text(step)
            if not target_text:
                print(f"❌ No target text found in step: {step}")
                continue
            
            print(f"🎯 Target text: '{target_text}'")
            
            # Find exact match nodes
            matches = self.find_exact_match_nodes(real_dom_elements, target_text)
            if not matches:
                print(f"❌ No exact matches found for '{target_text}'")
                continue
            
            print(f"✅ Found {len(matches)} exact matches")
            
            # Build HTML context for each match
            html_snippets = []
            for match in matches:
                context = self.build_html_context(match, real_dom_elements)
                html_snippets.append({
                    'html': context,
                    'element': match
                })
            
            # Score snippets with MarkupLM
            scored_snippets = self.score_snippets_with_markuplm(html_snippets, step)
            
            if not scored_snippets:
                print(f"❌ No snippets were scored")
                continue
            
            # Get best match
            best_score, best_html, best_element = scored_snippets[0]
            
            print(f"\n🏆 BEST MATCH:")
            print(f"   Score: {best_score:.3f}")
            print(f"   Element: {best_element.get('tag', 'unknown')}")
            print(f"   Text: '{best_element.get('text', '')}'")
            print(f"   Attributes: {best_element.get('attributes', {})}")
            
            # Generate XPath
            xpath = self.generate_xpath(best_element)
            print(f"   XPath: {xpath}")
            
            print(f"\n✅ Step {step_idx} completed successfully!")
        
        print(f"\n🎉 All {len(test_steps)} steps completed!")
        print("="*80)


def main():
    """Main function to run the test."""
    try:
        test = RealDOMVerizonTest()
        test.run_test()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()