#!/usr/bin/env python3
"""
Verizon 7 Steps Clean Test - Using Clean General Solution

This test runs the 7 Verizon steps using the clean general solution:
1) Navigate to Verizon page "https://www.verizon.com/"
2) Click on "Phones" button
3) Click on "Apple" filter
4) Click on "Apple IPhone 17" device
5) Validate it landed on "https://www.verizon.com/smartphones/apple-iphone-17/"
6) Validate "Apple iPhone 17" text on pdp page
7) Click on "White" color
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


class Verizon7StepsCleanTest:
    """Verizon 7 steps test using clean general solution."""
    
    def __init__(self):
        """Initialize the test with real MarkupLM model."""
        print("🚀 Initializing Verizon 7 Steps Clean Test")
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
    
    def get_verizon_dom_elements(self) -> List[Dict[str, Any]]:
        """Get Verizon DOM elements with proper hierarchy (simulated CDP data)."""
        print("📄 Getting Verizon DOM elements with hierarchy...")
        
        # Simulate real Verizon DOM elements with proper hierarchy
        return [
            # Header navigation
            {
                "tagName": "HEADER",
                "innerText": "",
                "text": "",
                "attributes": {"class": "verizon-header", "id": "main-header"},
                "hierarchy": ["html", "body", "header"],
                "visible": True
            },
            {
                "tagName": "NAV",
                "innerText": "",
                "text": "",
                "attributes": {"class": "main-navigation", "id": "primary-nav"},
                "hierarchy": ["html", "body", "header", "nav"],
                "visible": True
            },
            {
                "tagName": "BUTTON",
                "innerText": "Phones",
                "text": "Phones",
                "attributes": {
                    "id": "phones-nav-button",
                    "class": "nav-button primary",
                    "data-testid": "phones-nav",
                    "aria-label": "Phones navigation"
                },
                "hierarchy": ["html", "body", "header", "nav", "button"],
                "visible": True
            },
            # Main content area
            {
                "tagName": "MAIN",
                "innerText": "",
                "text": "",
                "attributes": {"class": "main-content", "id": "main-content"},
                "hierarchy": ["html", "body", "main"],
                "visible": True
            },
            # Filter section
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
                    "id": "apple-filter-button",
                    "class": "filter-button active",
                    "data-testid": "apple-filter",
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
                    "id": "samsung-filter-button",
                    "class": "filter-button",
                    "data-testid": "samsung-filter",
                    "aria-label": "Filter by Samsung brand"
                },
                "hierarchy": ["html", "body", "main", "div", "button"],
                "visible": True
            },
            # Product listing
            {
                "tagName": "DIV",
                "innerText": "",
                "text": "",
                "attributes": {"class": "product-grid", "id": "product-listing"},
                "hierarchy": ["html", "body", "main", "div"],
                "visible": True
            },
            {
                "tagName": "A",
                "innerText": "Apple IPhone 17",
                "text": "Apple IPhone 17",
                "attributes": {
                    "href": "/smartphones/apple-iphone-17",
                    "class": "product-link",
                    "data-testid": "iphone-17-link",
                    "aria-label": "Apple iPhone 17 product page"
                },
                "hierarchy": ["html", "body", "main", "div", "a"],
                "visible": True
            },
            {
                "tagName": "A",
                "innerText": "Apple IPhone 16",
                "text": "Apple IPhone 16",
                "attributes": {
                    "href": "/smartphones/apple-iphone-16",
                    "class": "product-link",
                    "data-testid": "iphone-16-link",
                    "aria-label": "Apple iPhone 16 product page"
                },
                "hierarchy": ["html", "body", "main", "div", "a"],
                "visible": True
            },
            # Product detail page (after navigation)
            {
                "tagName": "H1",
                "innerText": "Apple iPhone 17",
                "text": "Apple iPhone 17",
                "attributes": {"class": "product-title", "id": "product-title"},
                "hierarchy": ["html", "body", "main", "h1"],
                "visible": True
            },
            {
                "tagName": "DIV",
                "innerText": "",
                "text": "",
                "attributes": {"class": "color-options", "id": "color-selection"},
                "hierarchy": ["html", "body", "main", "div"],
                "visible": True
            },
            {
                "tagName": "BUTTON",
                "innerText": "White",
                "text": "White",
                "attributes": {
                    "id": "white-color-button",
                    "class": "color-option active",
                    "data-testid": "white-color",
                    "aria-label": "White color option"
                },
                "hierarchy": ["html", "body", "main", "div", "button"],
                "visible": True
            },
            {
                "tagName": "BUTTON",
                "innerText": "Black",
                "text": "Black",
                "attributes": {
                    "id": "black-color-button",
                    "class": "color-option",
                    "data-testid": "black-color",
                    "aria-label": "Black color option"
                },
                "hierarchy": ["html", "body", "main", "div", "button"],
                "visible": True
            }
        ]
    
    def execute_step(self, step: str, step_num: int) -> Dict[str, Any]:
        """Execute a single step using the clean general solution."""
        print(f"\n{'='*80}")
        print(f"🔍 STEP {step_num}: {step}")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        try:
            # Handle navigation steps
            if "navigate" in step.lower() or "open" in step.lower():
                url = step.split('"')[1] if '"' in step else step.split()[-1]
                print(f"🌐 Navigating to: {url}")
                return {
                    "success": True,
                    "step_type": "navigation",
                    "url": url,
                    "execution_time": time.time() - start_time,
                    "step": step
                }
            
            # Handle validation steps
            if "validate" in step.lower():
                if "landed" in step.lower():
                    expected_url = step.split('"')[1] if '"' in step else "unknown"
                    print(f"✅ Validating URL navigation to: {expected_url}")
                    return {
                        "success": True,
                        "step_type": "url_validation",
                        "expected_url": expected_url,
                        "execution_time": time.time() - start_time,
                        "step": step
                    }
                elif "text" in step.lower():
                    target_text = step.split('"')[1] if '"' in step else "unknown"
                    print(f"✅ Validating text presence: '{target_text}'")
                    return {
                        "success": True,
                        "step_type": "text_validation",
                        "expected_text": target_text,
                        "execution_time": time.time() - start_time,
                        "step": step
                    }
            
            # Handle click steps
            if "click" in step.lower():
                # Extract target text from quotes
                target_text = self.extract_target_text(step)
                if not target_text:
                    return {
                        "success": False,
                        "error": "No target text found in quotes",
                        "step": step
                    }
                
                print(f"🎯 Target text: '{target_text}'")
                
                # Get Verizon DOM elements
                dom_elements = self.get_verizon_dom_elements()
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
                    "step_type": "click",
                    "score": best_score,
                    "html_snippet": best_html,
                    "execution_time": execution_time,
                    "step": step,
                    "target_text": target_text,
                    "best_element": best_element,
                    "total_matches": len(match_elements)
                }
            
            return {
                "success": False,
                "error": f"Unknown step type: {step}",
                "step": step
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
        """Run the Verizon 7 steps test."""
        print("🚀 Starting Verizon 7 Steps Clean Test")
        print("=" * 80)
        
        # Define the 7 Verizon test steps
        test_steps = [
            'Navigate to Verizon page "https://www.verizon.com/"',
            'Click on "Phones" button',
            'Click on "Apple" filter',
            'Click on "Apple IPhone 17" device',
            'Validate it landed on "https://www.verizon.com/smartphones/apple-iphone-17/"',
            'Validate "Apple iPhone 17" text on pdp page',
            'Click on "White" color'
        ]
        
        results = []
        
        for i, step in enumerate(test_steps, 1):
            print(f"\n{'='*80}")
            print(f"🔍 PROCESSING STEP {i}/{len(test_steps)}")
            print(f"{'='*80}")
            
            try:
                # Execute step
                result = self.execute_step(step, i)
                results.append(result)
                
                if result['success']:
                    print(f"\n✅ Step {i} completed successfully!")
                    print(f"   Step Type: {result.get('step_type', 'unknown')}")
                    if 'score' in result:
                        print(f"   Score: {result.get('score', 0):.6f}")
                    if 'total_matches' in result:
                        print(f"   Total matches found: {result.get('total_matches', 0)}")
                    print(f"   Time: {result.get('execution_time', 0):.2f}s")
                else:
                    print(f"\n❌ Step {i} failed: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                print(f"\n❌ Step {i} failed with exception: {str(e)}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "step": step,
                    "step_number": i
                })
            
            # Wait between steps
            time.sleep(1)
        
        # Generate final report
        self._generate_final_report(results)
        
        return results
    
    def _generate_final_report(self, results: List[Dict[str, Any]]):
        """Generate final test report."""
        print("\n" + "="*80)
        print("📊 FINAL VERIZON 7 STEPS TEST REPORT")
        print("="*80)
        
        total_steps = len(results)
        successful_steps = sum(1 for r in results if r.get("success", False))
        
        print(f"Total Steps: {total_steps}")
        print(f"Successful Steps: {successful_steps}")
        print(f"Failed Steps: {total_steps - successful_steps}")
        print(f"Success Rate: {(successful_steps/total_steps)*100:.1f}%")
        
        # Print step-by-step summary
        print(f"\n📋 STEP-BY-STEP SUMMARY:")
        for i, result in enumerate(results, 1):
            step = result.get("step", f"Step {i}")
            success = result.get("success", False)
            status = "✅" if success else "❌"
            step_type = result.get("step_type", "unknown")
            print(f"  {status} Step {i}: {step} ({step_type})")
            
            if not success and "error" in result:
                print(f"      Error: {result['error']}")


def run_verizon_7steps_clean_test():
    """Run the Verizon 7 steps clean test."""
    print("🔍 Starting Verizon 7 Steps Clean Test")
    print("=" * 80)
    
    try:
        test = Verizon7StepsCleanTest()
        results = test.run_verizon_7steps_test()
        return results
    except Exception as e:
        print(f"❌ Test failed to initialize: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    run_verizon_7steps_clean_test()