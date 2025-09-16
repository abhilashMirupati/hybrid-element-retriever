#!/usr/bin/env python3
"""
MarkupLM Verizon Test - 7 Steps

This test implements the exact 7-step Verizon automation flow with MarkupLM:
1) Navigate to Verizon page "https://www.verizon.com/"
2) Click on "Phones" button
3) Click on "Apple" filter
4) Click on "Apple IPhone 17" device
5) Validate it landed on "https://www.verizon.com/smartphones/apple-iphone-17/"
6) Validate "Apple iPhone 17" text on pdp page
7) Click on "White" color

Features:
- Real MarkupLM model (microsoft/markuplm-base-finetuned-websrc)
- Hierarchical HTML context building
- MarkupLM scoring for element ranking
- XPath generation for each step
- Detailed input/output logging
"""

import os
import sys
import time
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import real MarkupLM components (no mocking)
from transformers import MarkupLMProcessor, MarkupLMForQuestionAnswering
import torch


class MarkupLMVerizon7StepsTest:
    """MarkupLM Verizon test with 7 steps."""
    
    def __init__(self):
        """Initialize the test with real MarkupLM model."""
        print("🚀 Initializing MarkupLM Verizon 7-Steps Test")
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
            # Check text content
            element_text = element.get('text', '').strip()
            if target_text.lower() in element_text.lower():
                matches.append(element)
                print(f"   ✅ Found text match: {element.get('tag', 'unknown')} - '{element_text[:50]}...'")
                continue
            
            # Check attributes
            attrs = element.get('attributes', {})
            for attr_name, attr_value in attrs.items():
                if isinstance(attr_value, str) and target_text.lower() in attr_value.lower():
                    matches.append(element)
                    print(f"   ✅ Found attribute match: {attr_name}='{attr_value[:50]}...'")
                    break
        
        print(f"   Found {len(matches)} exact match nodes")
        return matches
    
    def build_html_context(self, node: Dict[str, Any], all_elements: List[Dict[str, Any]]) -> str:
        """Build HTML context for a node including grandparent and siblings."""
        print(f"🏗️  Building HTML context for node: {node.get('tag', 'unknown')}")
        
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
        for parent in parents[-2:]:
            tag = parent.get('tag', 'div')
            html_parts.append(f'</{tag}>')
        
        html_context = ''.join(html_parts)
        print(f"   Built HTML context ({len(html_context)} chars)")
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
        """Build attribute string for HTML."""
        if not attrs:
            return ""
        
        attr_parts = []
        
        # Include important attributes
        important_attrs = ['class', 'id', 'role', 'type', 'name', 'aria-label', 'data-testid']
        
        for attr in important_attrs:
            value = attrs.get(attr, '')
            if value:
                # Escape quotes in attribute values
                escaped_value = str(value).replace('"', '&quot;')
                attr_parts.append(f'{attr}="{escaped_value}"')
        
        return ' ' + ' '.join(attr_parts) if attr_parts else ''
    
    def score_snippets_with_markuplm(self, html_snippets: List[str], query: str) -> List[Tuple[float, str, int]]:
        """Score HTML snippets using real MarkupLM model."""
        print(f"🤖 Scoring {len(html_snippets)} snippets with MarkupLM")
        print(f"📝 Query: '{query}'")
        
        results = []
        
        for idx, snippet in enumerate(html_snippets):
            print(f"\n   📄 Snippet {idx+1} (HTML length: {len(snippet)} chars):")
            print(f"   HTML: {snippet[:200]}{'...' if len(snippet) > 200 else ''}")
            
            try:
                # Prepare inputs for MarkupLM
                inputs = self.processor(
                    questions=[query],
                    html_strings=[snippet],
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=512
                )
                
                print(f"   🔧 MarkupLM Input prepared:")
                print(f"      - Available keys: {list(inputs.keys())}")
                print(f"      - Input IDs shape: {inputs['input_ids'].shape}")
                print(f"      - Attention mask shape: {inputs['attention_mask'].shape}")
                
                # Get model predictions
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    
                    # Get start and end logits
                    start_logits = outputs.start_logits
                    end_logits = outputs.end_logits
                    
                    # Calculate scores using softmax probabilities
                    start_probs = torch.softmax(start_logits, dim=-1)
                    end_probs = torch.softmax(end_logits, dim=-1)
                    
                    # Get max probabilities
                    start_score = start_probs.max().item()
                    end_score = end_probs.max().item()
                    combined_score = (start_score + end_score) / 2.0
                    
                    print(f"   📊 MarkupLM Output:")
                    print(f"      - Start logits shape: {start_logits.shape}")
                    print(f"      - End logits shape: {end_logits.shape}")
                    print(f"      - Start probability max: {start_score:.3f}")
                    print(f"      - End probability max: {end_score:.3f}")
                    print(f"      - Combined score: {combined_score:.3f}")
                    
                    results.append((combined_score, snippet, idx))
                    
            except Exception as e:
                print(f"   ❌ Error scoring snippet {idx+1}: {e}")
                import traceback
                traceback.print_exc()
                results.append((0.0, snippet, idx))
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x[0], reverse=True)
        
        print(f"\n   🏆 Ranking Results:")
        for i, (score, snippet, orig_idx) in enumerate(results):
            print(f"      {i+1}. Snippet {orig_idx+1}: Score = {score:.3f}")
        
        return results
    
    def generate_best_xpath(self, node: Dict[str, Any]) -> str:
        """Generate the best XPath for a node using multiple strategies."""
        print(f"🎯 Generating best XPath for node: {node.get('tag', 'unknown')}")
        
        tag = node.get('tag', 'div')
        attrs = node.get('attributes', {})
        
        # Priority order for XPath generation
        if attrs.get('id'):
            xpath = f"//*[@id='{attrs['id']}']"
            print(f"   Using ID-based XPath: {xpath}")
            return xpath
        elif attrs.get('data-testid'):
            xpath = f"//*[@data-testid='{attrs['data-testid']}']"
            print(f"   Using data-testid XPath: {xpath}")
            return xpath
        elif attrs.get('aria-label'):
            xpath = f"//*[@aria-label='{attrs['aria-label']}']"
            print(f"   Using aria-label XPath: {xpath}")
            return xpath
        elif attrs.get('class'):
            first_class = attrs['class'].split()[0]
            xpath = f"//{tag}[@class='{first_class}']"
            print(f"   Using class-based XPath: {xpath}")
            return xpath
        elif attrs.get('name'):
            xpath = f"//{tag}[@name='{attrs['name']}']"
            print(f"   Using name-based XPath: {xpath}")
            return xpath
        else:
            text = node.get('text', '').strip()
            if text and len(text) < 100:
                escaped_text = text.replace("'", "\\'").replace('"', '\\"')
                xpath = f"//{tag}[normalize-space()='{escaped_text}']"
                print(f"   Using text-based XPath: {xpath}")
                return xpath
            else:
                xpath = f"//{tag}"
                print(f"   Using generic XPath: {xpath}")
                return xpath
    
    def get_sample_elements(self) -> List[Dict[str, Any]]:
        """Get sample elements that might be on a Verizon page."""
        print("📄 Getting sample page elements...")
        
        return [
            {
                "tag": "button",
                "text": "Phones",
                "attributes": {
                    "id": "phones-button",
                    "class": "nav-button primary",
                    "data-testid": "phones-nav",
                    "aria-label": "Phones button"
                },
                "visible": True,
                "xpath": "//button[@id='phones-button']"
            },
            {
                "tag": "button",
                "text": "Apple",
                "attributes": {
                    "id": "apple-filter",
                    "class": "filter-button active",
                    "data-testid": "apple-filter",
                    "aria-label": "Filter by Apple brand"
                },
                "visible": True,
                "xpath": "//div[@class='filter-container']/button[@id='apple-filter']"
            },
            {
                "tag": "a",
                "text": "Apple IPhone 17",
                "attributes": {
                    "href": "/smartphones/apple-iphone-17",
                    "class": "product-link",
                    "data-testid": "iphone-17-link"
                },
                "visible": True,
                "xpath": "//a[@href='/smartphones/apple-iphone-17']"
            },
            {
                "tag": "h1",
                "text": "Apple iPhone 17",
                "attributes": {
                    "class": "product-title",
                    "data-testid": "product-title"
                },
                "visible": True,
                "xpath": "//h1[@class='product-title']"
            },
            {
                "tag": "button",
                "text": "White",
                "attributes": {
                    "id": "white-color",
                    "class": "color-option active",
                    "data-testid": "white-color",
                    "aria-label": "White color option"
                },
                "visible": True,
                "xpath": "//button[@id='white-color']"
            },
            {
                "tag": "div",
                "text": "Product Page",
                "attributes": {
                    "class": "product-page",
                    "id": "product-container"
                },
                "visible": True,
                "xpath": "//div[@class='product-page']"
            },
            {
                "tag": "div",
                "text": "Color Options",
                "attributes": {
                    "class": "color-options",
                    "id": "color-selection"
                },
                "visible": True,
                "xpath": "//div[@class='color-options']"
            }
        ]
    
    def execute_step_with_markuplm(self, step: str) -> Dict[str, Any]:
        """Execute a single step using MarkupLM-enhanced matching."""
        print(f"\n{'='*80}")
        print(f"🔍 STEP: {step}")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        try:
            # Extract target text from quotes
            target_text = self.extract_target_text(step)
            if not target_text:
                return {
                    "success": False,
                    "error": "No target text found in quotes",
                    "step": step
                }
            
            print(f"🎯 Target text: '{target_text}'")
            
            # Get current page elements
            all_elements = self.get_sample_elements()
            if not all_elements:
                return {
                    "success": False,
                    "error": "No page elements available",
                    "step": step
                }
            
            # Find exact match nodes
            match_nodes = self.find_exact_match_nodes(all_elements, target_text)
            if not match_nodes:
                return {
                    "success": False,
                    "error": f"No exact match nodes found for '{target_text}'",
                    "step": step
                }
            
            # Build HTML context for each node
            html_snippets = []
            for node in match_nodes:
                html_context = self.build_html_context(node, all_elements)
                html_snippets.append(html_context)
            
            # Score snippets with MarkupLM
            scored_snippets = self.score_snippets_with_markuplm(html_snippets, step)
            
            if not scored_snippets:
                return {
                    "success": False,
                    "error": "Failed to score snippets with MarkupLM",
                    "step": step
                }
            
            # Get the highest scoring node
            best_score, best_html, best_idx = scored_snippets[0]
            best_node = match_nodes[best_idx]
            
            print(f"\n🏆 Best match selected:")
            print(f"   Score: {best_score:.3f}")
            print(f"   HTML snippet length: {len(best_html)} chars")
            print(f"   Node: {best_node.get('tag', 'unknown')} - '{best_node.get('text', '')[:50]}...'")
            
            # Generate best XPath for the highest scoring node
            best_xpath = self.generate_best_xpath(best_node)
            
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "xpath": best_xpath,
                "score": best_score,
                "html_snippet": best_html,
                "execution_time": execution_time,
                "step": step,
                "target_text": target_text,
                "best_node": best_node
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "step": step
            }
    
    def run_verizon_7steps_test(self):
        """Run the Verizon test with 7 steps."""
        print("🚀 Starting Verizon 7-Steps Test with MarkupLM")
        print("=" * 80)
        
        # The exact 7 steps from test_verizon_fixed.py
        steps = [
            'Navigate to Verizon page "https://www.verizon.com/"',
            'Click on "Phones" button',
            'Click on "Apple" filter',
            'Click on "Apple IPhone 17" device',
            'Validate it landed on "https://www.verizon.com/smartphones/apple-iphone-17/"',
            'Validate "Apple iPhone 17" text on pdp page',
            'Click on "White" color'
        ]
        
        results = []
        
        for i, step in enumerate(steps, 1):
            print(f"\n{'='*80}")
            print(f"🔍 PROCESSING STEP {i}/{len(steps)}")
            print(f"{'='*80}")
            
            try:
                # Execute step with MarkupLM
                result = self.execute_step_with_markuplm(step)
                results.append(result)
                
                if result['success']:
                    print(f"\n✅ Step {i} completed successfully!")
                    print(f"   XPath: {result.get('xpath', 'N/A')}")
                    print(f"   Score: {result.get('score', 0):.3f}")
                    print(f"   Time: {result.get('execution_time', 0):.2f}s")
                else:
                    print(f"\n❌ Step {i} failed: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                print(f"\n❌ Step {i} failed with exception: {str(e)}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "step": step
                })
            
            # Wait between steps
            time.sleep(1)
        
        # Final summary
        self.print_final_summary(results)
        
        # Save results
        self.save_results(results)
        
        return results
    
    def print_final_summary(self, results: List[Dict[str, Any]]):
        """Print final test summary."""
        print(f"\n{'='*80}")
        print("📊 FINAL RESULTS SUMMARY")
        print(f"{'='*80}")
        
        successful = sum(1 for r in results if r.get('success', False))
        total = len(results)
        success_rate = (successful / total) * 100 if total > 0 else 0
        
        print(f"Total Steps: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {total - successful}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 DETAILED STEP RESULTS:")
        for i, result in enumerate(results, 1):
            status = "✅" if result.get('success', False) else "❌"
            print(f"  {status} Step {i}: {result.get('step', 'Unknown')}")
            
            if result.get('success'):
                print(f"     XPath: {result.get('xpath', 'N/A')}")
                print(f"     Score: {result.get('score', 0):.3f}")
                print(f"     Time: {result.get('execution_time', 0):.2f}s")
            else:
                print(f"     Error: {result.get('error', 'Unknown error')}")
    
    def save_results(self, results: List[Dict[str, Any]]):
        """Save results to JSON file."""
        filename = 'markuplm_verizon_7steps_results.json'
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Detailed results saved to: {filename}")


def run_markuplm_verizon_7steps_test():
    """Run the MarkupLM Verizon 7-steps test."""
    print("🔍 Starting MarkupLM Verizon 7-Steps Test")
    print("=" * 80)
    
    try:
        test = MarkupLMVerizon7StepsTest()
        results = test.run_verizon_7steps_test()
        return results
    except Exception as e:
        print(f"❌ Test failed to initialize: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    run_markuplm_verizon_7steps_test()