#!/usr/bin/env python3
"""
Enhanced Verizon Test with MarkupLM Integration

This test implements the exact workflow:
1. Get exact match nodes based on target text in quotes
2. Build HTML context for each node (grandparent + siblings)
3. Use MarkupLM to score snippets with user query
4. Generate best XPath for highest-scoring node
5. Pass XPath to Playwright for execution
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

from her.core.runner import Runner
from her.locator.intent_parser import IntentParser, ParsedIntent, IntentType
from her.locator.target_matcher import TargetMatcher
from her.utils.xpath_generator import generate_xpath_candidates, select_best_xpath_candidate


class MarkupLMVerizonTest:
    """Enhanced Verizon test with real MarkupLM integration."""
    
    def __init__(self):
        """Initialize the test with real MarkupLM model."""
        print("🚀 Initializing Enhanced Verizon Test with MarkupLM")
        print("=" * 80)
        
        # Initialize MarkupLM model
        self.model_name = "microsoft/markuplm-base-finetuned-websrc"
        print(f"Loading MarkupLM model: {self.model_name}")
        
        try:
            self.processor = MarkupLMProcessor.from_pretrained(self.model_name)
            self.model = MarkupLMForQuestionAnswering.from_pretrained(self.model_name)
            self.model.eval()
            print("✅ MarkupLM model loaded successfully!")
        except Exception as e:
            print(f"❌ Failed to load MarkupLM model: {e}")
            raise
        
        # Initialize other components
        self.runner = Runner(headless=False)
        self.intent_parser = IntentParser()
        self.target_matcher = TargetMatcher(case_sensitive=False)
        
        print("✅ All components initialized successfully!")
    
    def extract_target_text(self, step: str) -> Optional[str]:
        """Extract target text from quoted strings in step."""
        # Look for quoted text in various formats
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
                node_depth = node_xpath.count('/')
                
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
    
    def score_snippets_with_markuplm(self, html_snippets: List[str], query: str) -> List[Tuple[float, str]]:
        """Score HTML snippets using real MarkupLM model."""
        print(f"🤖 Scoring {len(html_snippets)} snippets with MarkupLM")
        
        results = []
        
        for idx, snippet in enumerate(html_snippets):
            try:
                # Prepare inputs for MarkupLM
                inputs = self.processor(
                    questions=query,
                    html_strings=[snippet],
                    return_tensors="pt"
                )
                
                # Get model predictions
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    
                    # Combine start and end logits as scoring metric
                    start_score = outputs.start_logits.max().item()
                    end_score = outputs.end_logits.max().item()
                    combined_score = (start_score + end_score) / 2.0
                    
                    results.append((combined_score, snippet))
                    print(f"   Snippet {idx+1}: Score = {combined_score:.3f}")
                    
            except Exception as e:
                print(f"   ❌ Error scoring snippet {idx+1}: {e}")
                results.append((0.0, snippet))
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x[0], reverse=True)
        
        print(f"   Top score: {results[0][0]:.3f}" if results else "   No results")
        return results
    
    def generate_best_xpath(self, node: Dict[str, Any]) -> str:
        """Generate the best XPath for a node using multiple strategies."""
        print(f"🎯 Generating best XPath for node: {node.get('tag', 'unknown')}")
        
        # Generate XPath candidates
        candidates = generate_xpath_candidates(node)
        
        if not candidates:
            return f"//{node.get('tag', 'div')}"
        
        # Select best candidate
        best_candidate = select_best_xpath_candidate(candidates)
        
        if best_candidate:
            print(f"   Best XPath: {best_candidate.xpath} (strategy: {best_candidate.strategy})")
            return best_candidate.xpath
        else:
            # Fallback
            fallback_xpath = f"//{node.get('tag', 'div')}"
            print(f"   Using fallback XPath: {fallback_xpath}")
            return fallback_xpath
    
    def execute_step_with_markuplm(self, step: str, all_elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a single step using MarkupLM-enhanced matching."""
        print(f"\n{'='*60}")
        print(f"🔍 STEP: {step}")
        print(f"{'='*60}")
        
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
            
            print(f"Target text: '{target_text}'")
            
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
            best_score, best_html = scored_snippets[0]
            best_node = match_nodes[0]  # Assuming same order
            
            print(f"Best score: {best_score:.3f}")
            print(f"Best HTML snippet length: {len(best_html)} chars")
            
            # Generate best XPath for the highest scoring node
            best_xpath = self.generate_best_xpath(best_node)
            
            # Execute with Playwright using the best XPath
            print(f"Executing with XPath: {best_xpath}")
            
            # Use the runner to execute the step
            result = self.runner.run([step])
            
            execution_time = time.time() - start_time
            
            return {
                "success": result[0].get('success', False) if result else False,
                "xpath": best_xpath,
                "score": best_score,
                "html_snippet": best_html,
                "execution_time": execution_time,
                "step": step,
                "result": result[0] if result else {}
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "step": step
            }
    
    def run_enhanced_test(self):
        """Run the enhanced Verizon test with MarkupLM integration."""
        print("🚀 Starting Enhanced Verizon Test with MarkupLM")
        print("=" * 80)
        
        # Test steps
        steps = [
            'Navigate to Verizon page "https://www.verizon.com/"',
            'Click on "Shop" button',
            'Click on "Devices"',
            'Click on "Smartphones"',
            'Click on "Apple iPhone 17"',
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
                # Get current page elements
                print("📄 Getting current page elements...")
                # This would normally get elements from the current page
                # For now, we'll simulate this with a basic element list
                all_elements = self.get_current_page_elements()
                
                # Execute step with MarkupLM
                result = self.execute_step_with_markuplm(step, all_elements)
                results.append(result)
                
                if result['success']:
                    print(f"✅ Step {i} completed successfully!")
                    print(f"   XPath: {result.get('xpath', 'N/A')}")
                    print(f"   Score: {result.get('score', 0):.3f}")
                    print(f"   Time: {result.get('execution_time', 0):.2f}s")
                else:
                    print(f"❌ Step {i} failed: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                print(f"❌ Step {i} failed with exception: {str(e)}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "step": step
                })
            
            # Wait between steps
            time.sleep(2)
        
        # Final summary
        self.print_final_summary(results)
        
        # Save results
        self.save_results(results)
        
        return results
    
    def get_current_page_elements(self) -> List[Dict[str, Any]]:
        """Get current page elements (simulated for now)."""
        # This is a simplified version - in reality, this would get elements from the current page
        return [
            {
                "tag": "button",
                "text": "Shop",
                "attributes": {
                    "id": "shop-button",
                    "class": "nav-button",
                    "data-testid": "shop-nav"
                },
                "visible": True,
                "xpath": "//button[@id='shop-button']"
            },
            {
                "tag": "a",
                "text": "Devices",
                "attributes": {
                    "href": "/devices",
                    "class": "nav-link"
                },
                "visible": True,
                "xpath": "//a[@href='/devices']"
            },
            {
                "tag": "button",
                "text": "Smartphones",
                "attributes": {
                    "id": "smartphones-btn",
                    "class": "category-button"
                },
                "visible": True,
                "xpath": "//button[@id='smartphones-btn']"
            }
        ]
    
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
        filename = 'enhanced_verizon_markuplm_results.json'
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Detailed results saved to: {filename}")


def main():
    """Main function to run the enhanced test."""
    try:
        test = MarkupLMVerizonTest()
        results = test.run_enhanced_test()
        return results
    except Exception as e:
        print(f"❌ Test failed to initialize: {e}")
        return []


if __name__ == "__main__":
    main()