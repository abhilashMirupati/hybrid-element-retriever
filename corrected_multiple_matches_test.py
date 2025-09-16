#!/usr/bin/env python3
"""
Corrected Multiple Exact Matches Test - Fixed HTML Context Building

This test fixes the HTML context building logic to properly handle multiple elements with same text.
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


class CorrectedMultipleExactMatchesTest:
    """Test that handles multiple elements with same exact text - CORRECTED VERSION."""
    
    def __init__(self):
        """Initialize the test with real MarkupLM model."""
        print("🚀 Initializing Corrected Multiple Exact Matches Test")
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
        """Find exact match nodes based on target text - handles multiple matches."""
        print(f"🔍 Finding EXACT match nodes for target: '{target_text}'")
        
        matches = []
        for element in elements:
            element_text = element.get('text', '').strip()
            
            # EXACT text match (case-insensitive)
            if target_text.lower() == element_text.lower():
                matches.append(element)
                print(f"   ✅ Found EXACT text match: {element.get('tag', 'unknown')} - '{element_text}' (ID: {element.get('attributes', {}).get('id', 'no-id')})")
                continue
            
            # Check for exact match in important attributes only
            attrs = element.get('attributes', {})
            important_attrs = ['aria-label', 'title', 'alt']
            
            for attr_name in important_attrs:
                attr_value = attrs.get(attr_name, '')
                if isinstance(attr_value, str) and target_text.lower() == attr_value.lower():
                    matches.append(element)
                    print(f"   ✅ Found EXACT attribute match: {attr_name}='{attr_value}' (ID: {attrs.get('id', 'no-id')})")
                    break
        
        print(f"   Found {len(matches)} EXACT match nodes")
        return matches
    
    def build_html_context(self, node: Dict[str, Any], all_elements: List[Dict[str, Any]]) -> str:
        """Build HTML context for a node including grandparent and siblings - CORRECTED VERSION."""
        print(f"🏗️  Building HTML context for node: {node.get('tag', 'unknown')} (ID: {node.get('attributes', {}).get('id', 'no-id')})")
        print(f"   Node text: '{node.get('text', '')}'")
        
        # Find parent elements (up to grandparent level)
        parents = self.find_parent_elements_corrected(node, all_elements)
        print(f"   Found {len(parents)} parent elements")
        
        # Find sibling elements
        siblings = self.find_sibling_elements_corrected(node, all_elements, parents)
        print(f"   Found {len(siblings)} sibling elements")
        
        # Build HTML structure
        html_parts = []
        
        # Add grandparent context
        for parent in parents[-2:]:  # Last 2 parents (parent + grandparent)
            tag = parent.get('tag', 'div')
            attrs = parent.get('attributes', {})
            attr_str = self.build_attribute_string(attrs)
            html_parts.append(f'<{tag}{attr_str}>')
            print(f"   Added parent: <{tag}{attr_str}>")
        
        # Add sibling context
        if siblings:
            html_parts.append('<div class="sibling-context">')
            for sibling in siblings[:5]:  # Limit to 5 siblings
                tag = sibling.get('tag', 'span')
                text = sibling.get('text', '')[:50]  # Truncate long text
                attrs = sibling.get('attributes', {})
                attr_str = self.build_attribute_string(attrs)
                html_parts.append(f'<{tag}{attr_str}>{text}</{tag}>')
                print(f"   Added sibling: <{tag}{attr_str}>{text}</{tag}>")
            html_parts.append('</div>')
        
        # Add target node
        tag = node.get('tag', 'div')
        text = node.get('text', '')
        attrs = node.get('attributes', {})
        attr_str = self.build_attribute_string(attrs)
        html_parts.append(f'<{tag}{attr_str}>{text}</{tag}>')
        print(f"   Added target: <{tag}{attr_str}>{text}</{tag}>")
        
        # Close parent tags
        for parent in parents[-2:]:
            tag = parent.get('tag', 'div')
            html_parts.append(f'</{tag}>')
            print(f"   Closed parent: </{tag}>")
        
        html_context = ''.join(html_parts)
        print(f"   Built HTML context ({len(html_context)} chars)")
        print(f"   HTML: {html_context}")
        return html_context
    
    def find_parent_elements_corrected(self, node: Dict[str, Any], all_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find parent elements for a node - CORRECTED VERSION."""
        parents = []
        node_xpath = node.get('xpath', '')
        
        if not node_xpath:
            return parents
        
        print(f"   Looking for parents of: {node_xpath}")
        
        # Extract parent xpaths by removing the last part
        xpath_parts = node_xpath.split('/')
        if len(xpath_parts) <= 2:
            return parents
        
        # Build parent xpaths
        for i in range(1, len(xpath_parts) - 1):
            parent_xpath = '/'.join(xpath_parts[:len(xpath_parts) - i])
            if parent_xpath.startswith('//'):
                parent_xpath = parent_xpath[2:]  # Remove leading //
            
            print(f"   Looking for parent with xpath containing: {parent_xpath}")
            
            # Find element with matching xpath
            for elem in all_elements:
                if elem == node:
                    continue
                
                elem_xpath = elem.get('xpath', '')
                if elem_xpath and parent_xpath in elem_xpath:
                    parents.append(elem)
                    print(f"   Found parent: {elem.get('tag', 'unknown')} - {elem_xpath}")
                    break
            
            # Limit depth
            if len(parents) >= 3:  # Max 3 levels up
                break
        
        return parents
    
    def find_sibling_elements_corrected(self, node: Dict[str, Any], all_elements: List[Dict[str, Any]], 
                                       parents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find sibling elements for a node - CORRECTED VERSION."""
        siblings = []
        
        if not parents:
            return siblings
        
        # Find elements with same parent
        parent_xpath = parents[0].get('xpath', '') if parents else ''
        if not parent_xpath:
            return siblings
        
        print(f"   Looking for siblings with parent: {parent_xpath}")
        
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
                    print(f"   Found sibling: {elem.get('tag', 'unknown')} - {elem_xpath}")
                    
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
    
    def score_snippets_with_markuplm(self, html_snippets: List[str], query: str, elements: List[Dict[str, Any]]) -> List[Tuple[float, str, int, Dict[str, Any]]]:
        """Score HTML snippets using real MarkupLM model with element context."""
        print(f"🤖 Scoring {len(html_snippets)} snippets with MarkupLM")
        print(f"📝 Query: '{query}'")
        
        results = []
        
        for idx, snippet in enumerate(html_snippets):
            element = elements[idx]
            element_id = element.get('attributes', {}).get('id', f'element-{idx}')
            element_tag = element.get('tag', 'unknown')
            
            print(f"\n   📄 Snippet {idx+1} - {element_tag} (ID: {element_id}):")
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
                    
                    # Alternative scoring: sum of all probabilities (more comprehensive)
                    start_sum = start_probs.sum().item()
                    end_sum = end_probs.sum().item()
                    sum_score = (start_sum + end_sum) / 2.0
                    
                    # Alternative scoring: max of start and end separately
                    max_start = start_probs.max().item()
                    max_end = end_probs.max().item()
                    max_score = max(max_start, max_end)
                    
                    print(f"   📊 MarkupLM Output:")
                    print(f"      - Start probability max: {start_score:.6f}")
                    print(f"      - End probability max: {end_score:.6f}")
                    print(f"      - Combined score: {combined_score:.6f}")
                    print(f"      - Sum score: {sum_score:.6f}")
                    print(f"      - Max score: {max_score:.6f}")
                    
                    # Use combined score as primary, but log alternatives
                    results.append((combined_score, snippet, idx, element))
                    
            except Exception as e:
                print(f"   ❌ Error scoring snippet {idx+1}: {e}")
                results.append((0.0, snippet, idx, element))
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x[0], reverse=True)
        
        print(f"\n   🏆 Ranking Results:")
        for i, (score, snippet, orig_idx, element) in enumerate(results):
            element_id = element.get('attributes', {}).get('id', f'element-{orig_idx}')
            element_tag = element.get('tag', 'unknown')
            print(f"      {i+1}. {element_tag} (ID: {element_id}): Score = {score:.6f}")
        
        return results
    
    def get_sample_elements_with_duplicates(self) -> List[Dict[str, Any]]:
        """Get sample elements including duplicates (main + footer)."""
        print("📄 Getting sample page elements with duplicates...")
        
        return [
            # Main navigation
            {
                "tag": "button",
                "text": "Phones",
                "attributes": {
                    "id": "phones-button-main",
                    "class": "nav-button primary",
                    "data-testid": "phones-nav-main",
                    "aria-label": "Phones button"
                },
                "visible": True,
                "xpath": "//header//button[@id='phones-button-main']"
            },
            {
                "tag": "button",
                "text": "Apple",
                "attributes": {
                    "id": "apple-filter-main",
                    "class": "filter-button active",
                    "data-testid": "apple-filter-main",
                    "aria-label": "Filter by Apple brand"
                },
                "visible": True,
                "xpath": "//main//button[@id='apple-filter-main']"
            },
            {
                "tag": "a",
                "text": "Apple IPhone 17",
                "attributes": {
                    "href": "/smartphones/apple-iphone-17",
                    "class": "product-link",
                    "data-testid": "iphone-17-link-main"
                },
                "visible": True,
                "xpath": "//main//a[@href='/smartphones/apple-iphone-17']"
            },
            {
                "tag": "button",
                "text": "White",
                "attributes": {
                    "id": "white-color-main",
                    "class": "color-option active",
                    "data-testid": "white-color-main",
                    "aria-label": "White color option"
                },
                "visible": True,
                "xpath": "//main//button[@id='white-color-main']"
            },
            # Footer duplicates
            {
                "tag": "button",
                "text": "Phones",
                "attributes": {
                    "id": "phones-button-footer",
                    "class": "footer-button",
                    "data-testid": "phones-nav-footer",
                    "aria-label": "Phones button"
                },
                "visible": True,
                "xpath": "//footer//button[@id='phones-button-footer']"
            },
            {
                "tag": "button",
                "text": "Apple",
                "attributes": {
                    "id": "apple-filter-footer",
                    "class": "footer-filter-button",
                    "data-testid": "apple-filter-footer",
                    "aria-label": "Filter by Apple brand"
                },
                "visible": True,
                "xpath": "//footer//button[@id='apple-filter-footer']"
            },
            {
                "tag": "a",
                "text": "Apple IPhone 17",
                "attributes": {
                    "href": "/smartphones/apple-iphone-17",
                    "class": "footer-product-link",
                    "data-testid": "iphone-17-link-footer"
                },
                "visible": True,
                "xpath": "//footer//a[@href='/smartphones/apple-iphone-17']"
            },
            {
                "tag": "button",
                "text": "White",
                "attributes": {
                    "id": "white-color-footer",
                    "class": "footer-color-option",
                    "data-testid": "white-color-footer",
                    "aria-label": "White color option"
                },
                "visible": True,
                "xpath": "//footer//button[@id='white-color-footer']"
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
            
            # Get current page elements (including duplicates)
            all_elements = self.get_sample_elements_with_duplicates()
            if not all_elements:
                return {
                    "success": False,
                    "error": "No page elements available",
                    "step": step
                }
            
            # Find EXACT match nodes (should find multiple now)
            match_nodes = self.find_exact_match_nodes(all_elements, target_text)
            if not match_nodes:
                return {
                    "success": False,
                    "error": f"No EXACT match nodes found for '{target_text}'",
                    "step": step
                }
            
            # Build HTML context for each node
            html_snippets = []
            for node in match_nodes:
                html_context = self.build_html_context(node, all_elements)
                html_snippets.append(html_context)
            
            # Score snippets with MarkupLM
            scored_snippets = self.score_snippets_with_markuplm(html_snippets, step, match_nodes)
            
            if not scored_snippets:
                return {
                    "success": False,
                    "error": "Failed to score snippets with MarkupLM",
                    "step": step
                }
            
            # Get the highest scoring node
            best_score, best_html, best_idx, best_element = scored_snippets[0]
            
            print(f"\n🏆 Best match selected:")
            print(f"   Score: {best_score:.6f}")
            print(f"   HTML snippet length: {len(best_html)} chars")
            print(f"   Node: {best_element.get('tag', 'unknown')} (ID: {best_element.get('attributes', {}).get('id', 'no-id')}) - '{best_element.get('text', '')[:50]}...'")
            
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "score": best_score,
                "html_snippet": best_html,
                "execution_time": execution_time,
                "step": step,
                "target_text": target_text,
                "best_node": best_element,
                "total_matches": len(match_nodes)
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "step": step
            }
    
    def run_corrected_multiple_matches_test(self):
        """Run the corrected test with multiple exact matches."""
        print("🚀 Starting Corrected Multiple Exact Matches Test")
        print("=" * 80)
        
        # Test steps
        steps = [
            'Click on "Apple" filter',  # Focus on this step to test the fix
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
                    print(f"   Score: {result.get('score', 0):.6f}")
                    print(f"   Total matches found: {result.get('total_matches', 0)}")
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
        
        return results


def run_corrected_multiple_exact_matches_test():
    """Run the corrected multiple exact matches test."""
    print("🔍 Starting Corrected Multiple Exact Matches Test")
    print("=" * 80)
    
    try:
        test = CorrectedMultipleExactMatchesTest()
        results = test.run_corrected_multiple_matches_test()
        return results
    except Exception as e:
        print(f"❌ Test failed to initialize: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    run_corrected_multiple_exact_matches_test()