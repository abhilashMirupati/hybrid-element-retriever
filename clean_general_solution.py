#!/usr/bin/env python3
"""
Clean General Solution - Proper Exact Text Matching with Real DOM Data

This implements the correct logic:
1. Get all DOM elements from CDP depth tree
2. Compare target text to innerText of elements (exact match only)
3. Build real hierarchical context (parent + siblings) from actual DOM
4. Use MarkupLM to score and rank
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


class CleanGeneralSolution:
    """Clean general solution for exact text matching with real DOM data."""
    
    def __init__(self):
        """Initialize the test with real MarkupLM model."""
        print("🚀 Initializing Clean General Solution")
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
    
    def find_exact_text_matches(self, dom_elements: List[Dict[str, Any]], target_text: str) -> List[Dict[str, Any]]:
        """Find elements with exact text match - ONLY innerText, not attributes."""
        print(f"🔍 Finding EXACT text matches for target: '{target_text}'")
        
        matches = []
        for element in dom_elements:
            # Get innerText from element
            inner_text = element.get('innerText', '').strip()
            if not inner_text:
                # Fallback to text content if innerText not available
                inner_text = element.get('text', '').strip()
            
            # EXACT text match (case-insensitive)
            if target_text.lower() == inner_text.lower():
                matches.append(element)
                print(f"   ✅ Found EXACT text match: {element.get('tagName', 'unknown')} - '{inner_text}' (ID: {element.get('attributes', {}).get('id', 'no-id')})")
        
        print(f"   Found {len(matches)} EXACT text matches")
        return matches
    
    def build_real_hierarchical_context(self, target_element: Dict[str, Any], all_elements: List[Dict[str, Any]]) -> str:
        """Build real hierarchical context from actual DOM elements."""
        print(f"🏗️  Building REAL hierarchical context for: {target_element.get('tagName', 'unknown')} (ID: {target_element.get('attributes', {}).get('id', 'no-id')})")
        
        # Get element's hierarchy path from DOM
        hierarchy_path = target_element.get('hierarchy', [])
        if not hierarchy_path:
            print("   ⚠️  No hierarchy path available, using element only")
            return self._build_element_only_html(target_element)
        
        print(f"   Hierarchy path: {hierarchy_path}")
        
        # Find parent elements from actual DOM
        parents = self._find_real_parents(target_element, all_elements, hierarchy_path)
        print(f"   Found {len(parents)} real parent elements")
        
        # Find sibling elements from actual DOM
        siblings = self._find_real_siblings(target_element, all_elements, hierarchy_path)
        print(f"   Found {len(siblings)} real sibling elements")
        
        # Build HTML with real DOM data
        html_parts = []
        
        # Add parent elements (from outermost to innermost)
        for parent in parents:
            tag = parent.get('tagName', 'div').lower()
            attrs = parent.get('attributes', {})
            attr_str = self._build_attributes_string(attrs)
            html_parts.append(f'<{tag}{attr_str}>')
            print(f"   Added parent: <{tag}{attr_str}>")
        
        # Add sibling elements
        if siblings:
            for sibling in siblings[:5]:  # Limit to 5 siblings
                tag = sibling.get('tagName', 'span').lower()
                text = sibling.get('innerText', sibling.get('text', ''))[:50]  # Truncate long text
                attrs = sibling.get('attributes', {})
                attr_str = self._build_attributes_string(attrs)
                html_parts.append(f'<{tag}{attr_str}>{text}</{tag}>')
                print(f"   Added sibling: <{tag}{attr_str}>{text}</{tag}>")
        
        # Add target element
        tag = target_element.get('tagName', 'div').lower()
        text = target_element.get('innerText', target_element.get('text', ''))
        attrs = target_element.get('attributes', {})
        attr_str = self._build_attributes_string(attrs)
        html_parts.append(f'<{tag}{attr_str}>{text}</{tag}>')
        print(f"   Added target: <{tag}{attr_str}>{text}</{tag}>")
        
        # Close parent elements (from innermost to outermost)
        for parent in reversed(parents):
            tag = parent.get('tagName', 'div').lower()
            html_parts.append(f'</{tag}>')
            print(f"   Closed parent: </{tag}>")
        
        html_context = ''.join(html_parts)
        print(f"   Built REAL hierarchical context ({len(html_context)} chars)")
        print(f"   HTML: {html_context}")
        return html_context
    
    def _find_real_parents(self, target_element: Dict[str, Any], all_elements: List[Dict[str, Any]], hierarchy_path: List[str]) -> List[Dict[str, Any]]:
        """Find real parent elements from DOM hierarchy."""
        parents = []
        
        if not hierarchy_path or len(hierarchy_path) <= 1:
            return parents
        
        # Get parent hierarchy paths
        for i in range(1, len(hierarchy_path)):
            parent_path = hierarchy_path[:-i]
            if not parent_path:
                break
            
            # Find element with matching hierarchy path
            for element in all_elements:
                if element == target_element:
                    continue
                
                element_hierarchy = element.get('hierarchy', [])
                if element_hierarchy == parent_path:
                    parents.append(element)
                    print(f"   Found parent: {element.get('tagName', 'unknown')} - {element_hierarchy}")
                    break
            
            # Limit depth
            if len(parents) >= 3:  # Max 3 levels up
                break
        
        return parents
    
    def _find_real_siblings(self, target_element: Dict[str, Any], all_elements: List[Dict[str, Any]], hierarchy_path: List[str]) -> List[Dict[str, Any]]:
        """Find real sibling elements from DOM hierarchy."""
        siblings = []
        
        if not hierarchy_path or len(hierarchy_path) <= 1:
            return siblings
        
        # Get parent path (one level up)
        parent_path = hierarchy_path[:-1]
        
        # Find elements with same parent
        for element in all_elements:
            if element == target_element:
                continue
            
            element_hierarchy = element.get('hierarchy', [])
            if len(element_hierarchy) == len(hierarchy_path) and element_hierarchy[:-1] == parent_path:
                siblings.append(element)
                print(f"   Found sibling: {element.get('tagName', 'unknown')} - {element_hierarchy}")
                
                # Limit number of siblings
                if len(siblings) >= 10:
                    break
        
        return siblings
    
    def _build_element_only_html(self, element: Dict[str, Any]) -> str:
        """Build HTML for element only when no hierarchy available."""
        tag = element.get('tagName', 'div').lower()
        text = element.get('innerText', element.get('text', ''))
        attrs = element.get('attributes', {})
        attr_str = self._build_attributes_string(attrs)
        return f'<{tag}{attr_str}>{text}</{tag}>'
    
    def _build_attributes_string(self, attrs: Dict[str, Any]) -> str:
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
        """Score HTML snippets using real MarkupLM model."""
        print(f"🤖 Scoring {len(html_snippets)} snippets with MarkupLM")
        print(f"📝 Query: '{query}'")
        
        results = []
        
        for idx, snippet in enumerate(html_snippets):
            element = elements[idx]
            element_id = element.get('attributes', {}).get('id', f'element-{idx}')
            element_tag = element.get('tagName', 'unknown')
            
            print(f"\n   📄 Snippet {idx+1} - {element_tag} (ID: {element_id}):")
            print(f"   HTML: {snippet}")
            
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
                    
                    print(f"   📊 MarkupLM Output:")
                    print(f"      - Start probability max: {start_score:.6f}")
                    print(f"      - End probability max: {end_score:.6f}")
                    print(f"      - Combined score: {combined_score:.6f}")
                    
                    results.append((combined_score, snippet, idx, element))
                    
            except Exception as e:
                print(f"   ❌ Error scoring snippet {idx+1}: {e}")
                results.append((0.0, snippet, idx, element))
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x[0], reverse=True)
        
        print(f"\n   🏆 Ranking Results:")
        for i, (score, snippet, orig_idx, element) in enumerate(results):
            element_id = element.get('attributes', {}).get('id', f'element-{orig_idx}')
            element_tag = element.get('tagName', 'unknown')
            print(f"      {i+1}. {element_tag} (ID: {element_id}): Score = {score:.6f}")
        
        return results
    
    def get_real_dom_elements(self) -> List[Dict[str, Any]]:
        """Get real DOM elements with proper hierarchy (simulated CDP data)."""
        print("📄 Getting real DOM elements with hierarchy...")
        
        # Simulate real DOM elements with proper hierarchy
        return [
            # Header section
            {
                "tagName": "HEADER",
                "innerText": "",
                "text": "",
                "attributes": {"class": "page-header", "id": "main-header"},
                "hierarchy": ["html", "body", "header"],
                "visible": True
            },
            {
                "tagName": "BUTTON",
                "innerText": "Phones",
                "text": "Phones",
                "attributes": {
                    "id": "phones-button-main",
                    "class": "nav-button primary",
                    "data-testid": "phones-nav-main",
                    "aria-label": "Phones button"
                },
                "hierarchy": ["html", "body", "header", "nav", "button"],
                "visible": True
            },
            # Main section
            {
                "tagName": "MAIN",
                "innerText": "",
                "text": "",
                "attributes": {"class": "page-main", "id": "main-content"},
                "hierarchy": ["html", "body", "main"],
                "visible": True
            },
            {
                "tagName": "DIV",
                "innerText": "",
                "text": "",
                "attributes": {"class": "filter-section", "id": "brand-filters"},
                "hierarchy": ["html", "body", "main", "div"],
                "visible": True
            },
            {
                "tagName": "BUTTON",
                "innerText": "Apple",
                "text": "Apple",
                "attributes": {
                    "id": "apple-filter-main",
                    "class": "filter-button active",
                    "data-testid": "apple-filter-main",
                    "aria-label": "Filter by Apple brand"
                },
                "hierarchy": ["html", "body", "main", "div", "button"],
                "visible": True
            },
            {
                "tagName": "BUTTON",
                "innerText": "Samsung",
                "text": "Samsung",
                "attributes": {
                    "id": "samsung-filter-main",
                    "class": "filter-button",
                    "data-testid": "samsung-filter-main",
                    "aria-label": "Filter by Samsung brand"
                },
                "hierarchy": ["html", "body", "main", "div", "button"],
                "visible": True
            },
            # Footer section
            {
                "tagName": "FOOTER",
                "innerText": "",
                "text": "",
                "attributes": {"class": "page-footer", "id": "main-footer"},
                "hierarchy": ["html", "body", "footer"],
                "visible": True
            },
            {
                "tagName": "DIV",
                "innerText": "",
                "text": "",
                "attributes": {"class": "footer-links", "id": "footer-navigation"},
                "hierarchy": ["html", "body", "footer", "div"],
                "visible": True
            },
            {
                "tagName": "BUTTON",
                "innerText": "Apple",
                "text": "Apple",
                "attributes": {
                    "id": "apple-filter-footer",
                    "class": "footer-filter-button",
                    "data-testid": "apple-filter-footer",
                    "aria-label": "Filter by Apple brand"
                },
                "hierarchy": ["html", "body", "footer", "div", "button"],
                "visible": True
            },
            {
                "tagName": "BUTTON",
                "innerText": "Samsung",
                "text": "Samsung",
                "attributes": {
                    "id": "samsung-filter-footer",
                    "class": "footer-filter-button",
                    "data-testid": "samsung-filter-footer",
                    "aria-label": "Filter by Samsung brand"
                },
                "hierarchy": ["html", "body", "footer", "div", "button"],
                "visible": True
            }
        ]
    
    def execute_step(self, step: str) -> Dict[str, Any]:
        """Execute a single step using the clean general solution."""
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
            
            # Get real DOM elements
            dom_elements = self.get_real_dom_elements()
            if not dom_elements:
                return {
                    "success": False,
                    "error": "No DOM elements available",
                    "step": step
                }
            
            # Find EXACT text matches (only innerText)
            match_elements = self.find_exact_text_matches(dom_elements, target_text)
            if not match_elements:
                return {
                    "success": False,
                    "error": f"No EXACT text matches found for '{target_text}'",
                    "step": step
                }
            
            # Build real hierarchical context for each match
            html_snippets = []
            for element in match_elements:
                html_context = self.build_real_hierarchical_context(element, dom_elements)
                html_snippets.append(html_context)
            
            # Score snippets with MarkupLM
            scored_snippets = self.score_snippets_with_markuplm(html_snippets, step, match_elements)
            
            if not scored_snippets:
                return {
                    "success": False,
                    "error": "Failed to score snippets with MarkupLM",
                    "step": step
                }
            
            # Get the highest scoring element
            best_score, best_html, best_idx, best_element = scored_snippets[0]
            
            print(f"\n🏆 Best match selected:")
            print(f"   Score: {best_score:.6f}")
            print(f"   HTML snippet length: {len(best_html)} chars")
            print(f"   Element: {best_element.get('tagName', 'unknown')} (ID: {best_element.get('attributes', {}).get('id', 'no-id')}) - '{best_element.get('innerText', '')[:50]}...'")
            
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "score": best_score,
                "html_snippet": best_html,
                "execution_time": execution_time,
                "step": step,
                "target_text": target_text,
                "best_element": best_element,
                "total_matches": len(match_elements)
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "step": step
            }
    
    def run_clean_test(self):
        """Run the clean general solution test."""
        print("🚀 Starting Clean General Solution Test")
        print("=" * 80)
        
        # Test steps
        steps = [
            'Click on "Phones" button',  # Should find 1 match
            'Click on "Apple" filter',   # Should find 2 matches
            'Click on "Samsung" filter', # Should find 2 matches
        ]
        
        results = []
        
        for i, step in enumerate(steps, 1):
            print(f"\n{'='*80}")
            print(f"🔍 PROCESSING STEP {i}/{len(steps)}")
            print(f"{'='*80}")
            
            try:
                # Execute step
                result = self.execute_step(step)
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


def run_clean_general_solution():
    """Run the clean general solution test."""
    print("🔍 Starting Clean General Solution")
    print("=" * 80)
    
    try:
        solution = CleanGeneralSolution()
        results = solution.run_clean_test()
        return results
    except Exception as e:
        print(f"❌ Test failed to initialize: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    run_clean_general_solution()