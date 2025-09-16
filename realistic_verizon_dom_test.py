#!/usr/bin/env python3
"""
Realistic Verizon DOM Test - Proper DOM Structure

This test uses realistic DOM elements that would actually exist on a Verizon page.
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


class RealisticVerizonDOMTest:
    """Verizon test with realistic DOM structure."""
    
    def __init__(self):
        """Initialize the test with real MarkupLM model."""
        print("🚀 Initializing Realistic Verizon DOM Test")
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
        important_attrs = ['class', 'id', 'role', 'type', 'name', 'aria-label', 'data-testid', 'href']
        
        for attr in important_attrs:
            value = attrs.get(attr, '')
            if value:
                # Escape quotes in attribute values
                escaped_value = str(value).replace('"', '&quot;')
                attr_parts.append(f'{attr}="{escaped_value}"')
        
        return ' ' + ' '.join(attr_parts) if attr_parts else ''
    
    def generate_xpath_for_element(self, element: Dict[str, Any]) -> str:
        """Generate XPath for an element."""
        tag = element.get('tagName', 'div').lower()
        attrs = element.get('attributes', {})
        text = element.get('innerText', element.get('text', ''))
        
        # Priority order for XPath generation
        if attrs.get('id'):
            return f"//*[@id='{attrs['id']}']"
        elif attrs.get('data-testid'):
            return f"//*[@data-testid='{attrs['data-testid']}']"
        elif attrs.get('aria-label'):
            return f"//*[@aria-label='{attrs['aria-label']}']"
        elif attrs.get('href'):
            return f"//a[@href='{attrs['href']}']"
        elif attrs.get('class'):
            # Use first class for specificity
            first_class = attrs['class'].split()[0]
            return f"//{tag}[@class='{first_class}']"
        elif text and len(text) < 100:  # Avoid very long text
            # Escape quotes in text and use correct tag
            escaped_text = text.replace("'", "\\'").replace('"', '\\"')
            return f"//{tag}[normalize-space()='{escaped_text}']"
        else:
            # Generic fallback
            return f"//{tag}"
    
    def score_snippets_with_markuplm_detailed(self, html_snippets: List[str], query: str, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score HTML snippets using real MarkupLM model with detailed input/output."""
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
                
                print(f"   🔧 MARKUPLM INPUT:")
                print(f"      - Query: '{query}'")
                print(f"      - HTML: {snippet}")
                print(f"      - Input IDs shape: {inputs['input_ids'].shape}")
                print(f"      - Attention mask shape: {inputs['attention_mask'].shape}")
                print(f"      - Available keys: {list(inputs.keys())}")
                
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
                    
                    print(f"   📊 MARKUPLM OUTPUT:")
                    print(f"      - Start probability max: {start_score:.6f}")
                    print(f"      - End probability max: {end_score:.6f}")
                    print(f"      - Combined score: {combined_score:.6f}")
                    
                    # Generate XPath for this element
                    xpath = self.generate_xpath_for_element(element)
                    print(f"   🎯 XPATH GENERATED: {xpath}")
                    
                    # Store detailed results
                    result = {
                        'score': combined_score,
                        'snippet': snippet,
                        'idx': idx,
                        'element': element,
                        'xpath': xpath,
                        'markup_input': {
                            'query': query,
                            'html': snippet,
                            'input_ids_shape': inputs['input_ids'].shape,
                            'attention_mask_shape': inputs['attention_mask'].shape,
                            'available_keys': list(inputs.keys())
                        },
                        'markup_output': {
                            'start_prob_max': start_score,
                            'end_prob_max': end_score,
                            'combined_score': combined_score
                        }
                    }
                    
                    results.append(result)
                    
            except Exception as e:
                print(f"   ❌ Error scoring snippet {idx+1}: {e}")
                xpath = self.generate_xpath_for_element(element)
                results.append({
                    'score': 0.0,
                    'snippet': snippet,
                    'idx': idx,
                    'element': element,
                    'xpath': xpath,
                    'error': str(e)
                })
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"\n   🏆 RANKING RESULTS:")
        for i, result in enumerate(results):
            element_id = result['element'].get('attributes', {}).get('id', f'element-{result["idx"]}')
            element_tag = result['element'].get('tagName', 'unknown')
            print(f"      {i+1}. {element_tag} (ID: {element_id}): Score = {result['score']:.6f}, XPath = {result['xpath']}")
        
        return results
    
    def get_realistic_verizon_dom_elements(self) -> List[Dict[str, Any]]:
        """Get realistic Verizon DOM elements with proper structure."""
        print("📄 Getting realistic Verizon DOM elements...")
        
        # Realistic Verizon DOM structure
        return [
            # Header with navigation
            {
                "tagName": "HEADER",
                "innerText": "",
                "text": "",
                "attributes": {"class": "vgn-header", "id": "header"},
                "hierarchy": ["html", "body", "header"],
                "visible": True
            },
            {
                "tagName": "NAV",
                "innerText": "",
                "text": "",
                "attributes": {"class": "vgn-navigation", "id": "main-nav"},
                "hierarchy": ["html", "body", "header", "nav"],
                "visible": True
            },
            {
                "tagName": "UL",
                "innerText": "",
                "text": "",
                "attributes": {"class": "vgn-nav-list", "id": "nav-list"},
                "hierarchy": ["html", "body", "header", "nav", "ul"],
                "visible": True
            },
            {
                "tagName": "LI",
                "innerText": "",
                "text": "",
                "attributes": {"class": "vgn-nav-item", "id": "nav-item-phones"},
                "hierarchy": ["html", "body", "header", "nav", "ul", "li"],
                "visible": True
            },
            {
                "tagName": "A",
                "innerText": "Phones",
                "text": "Phones",
                "attributes": {
                    "href": "/smartphones/",
                    "class": "vgn-nav-link",
                    "id": "phones-nav-link",
                    "data-testid": "phones-nav",
                    "aria-label": "Shop phones"
                },
                "hierarchy": ["html", "body", "header", "nav", "ul", "li", "a"],
                "visible": True
            },
            # Main content area
            {
                "tagName": "MAIN",
                "innerText": "",
                "text": "",
                "attributes": {"class": "vgn-main", "id": "main-content"},
                "hierarchy": ["html", "body", "main"],
                "visible": True
            },
            # Filter section
            {
                "tagName": "DIV",
                "innerText": "",
                "text": "",
                "attributes": {"class": "vgn-filter-section", "id": "brand-filters"},
                "hierarchy": ["html", "body", "main", "div"],
                "visible": True
            },
            {
                "tagName": "DIV",
                "innerText": "",
                "text": "",
                "attributes": {"class": "vgn-filter-group", "id": "brand-filter-group"},
                "hierarchy": ["html", "body", "main", "div", "div"],
                "visible": True
            },
            {
                "tagName": "BUTTON",
                "innerText": "Apple",
                "text": "Apple",
                "attributes": {
                    "id": "apple-filter-btn",
                    "class": "vgn-filter-button active",
                    "data-testid": "apple-filter",
                    "aria-label": "Filter by Apple",
                    "aria-pressed": "true"
                },
                "hierarchy": ["html", "body", "main", "div", "div", "button"],
                "visible": True
            },
            {
                "tagName": "BUTTON",
                "innerText": "Samsung",
                "text": "Samsung",
                "attributes": {
                    "id": "samsung-filter-btn",
                    "class": "vgn-filter-button",
                    "data-testid": "samsung-filter",
                    "aria-label": "Filter by Samsung",
                    "aria-pressed": "false"
                },
                "hierarchy": ["html", "body", "main", "div", "div", "button"],
                "visible": True
            },
            # Product grid
            {
                "tagName": "DIV",
                "innerText": "",
                "text": "",
                "attributes": {"class": "vgn-product-grid", "id": "product-grid"},
                "hierarchy": ["html", "body", "main", "div"],
                "visible": True
            },
            {
                "tagName": "DIV",
                "innerText": "",
                "text": "",
                "attributes": {"class": "vgn-product-card", "id": "product-card-iphone17"},
                "hierarchy": ["html", "body", "main", "div", "div"],
                "visible": True
            },
            {
                "tagName": "A",
                "innerText": "Apple IPhone 17",
                "text": "Apple IPhone 17",
                "attributes": {
                    "href": "/smartphones/apple-iphone-17/",
                    "class": "vgn-product-link",
                    "id": "iphone-17-link",
                    "data-testid": "iphone-17-link",
                    "aria-label": "Apple iPhone 17 details"
                },
                "hierarchy": ["html", "body", "main", "div", "div", "a"],
                "visible": True
            },
            # Product detail page (after navigation)
            {
                "tagName": "H1",
                "innerText": "Apple iPhone 17",
                "text": "Apple iPhone 17",
                "attributes": {"class": "vgn-product-title", "id": "product-title"},
                "hierarchy": ["html", "body", "main", "h1"],
                "visible": True
            },
            {
                "tagName": "DIV",
                "innerText": "",
                "text": "",
                "attributes": {"class": "vgn-color-options", "id": "color-options"},
                "hierarchy": ["html", "body", "main", "div"],
                "visible": True
            },
            {
                "tagName": "BUTTON",
                "innerText": "White",
                "text": "White",
                "attributes": {
                    "id": "white-color-btn",
                    "class": "vgn-color-button active",
                    "data-testid": "white-color",
                    "aria-label": "White color",
                    "aria-pressed": "true"
                },
                "hierarchy": ["html", "body", "main", "div", "button"],
                "visible": True
            },
            {
                "tagName": "BUTTON",
                "innerText": "Black",
                "text": "Black",
                "attributes": {
                    "id": "black-color-btn",
                    "class": "vgn-color-button",
                    "data-testid": "black-color",
                    "aria-label": "Black color",
                    "aria-pressed": "false"
                },
                "hierarchy": ["html", "body", "main", "div", "button"],
                "visible": True
            }
        ]
    
    def execute_step_detailed(self, step: str, step_num: int) -> Dict[str, Any]:
        """Execute a single step with detailed MarkupLM input/output and XPath analysis."""
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
                    "step": step,
                    "xpath": "N/A (Navigation)",
                    "markup_input": "N/A (Navigation)",
                    "markup_output": "N/A (Navigation)"
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
                        "step": step,
                        "xpath": "N/A (URL Validation)",
                        "markup_input": "N/A (URL Validation)",
                        "markup_output": "N/A (URL Validation)"
                    }
                elif "text" in step.lower():
                    target_text = step.split('"')[1] if '"' in step else "unknown"
                    print(f"✅ Validating text presence: '{target_text}'")
                    return {
                        "success": True,
                        "step_type": "text_validation",
                        "expected_text": target_text,
                        "execution_time": time.time() - start_time,
                        "step": step,
                        "xpath": "N/A (Text Validation)",
                        "markup_input": "N/A (Text Validation)",
                        "markup_output": "N/A (Text Validation)"
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
                
                # Get realistic Verizon DOM elements
                dom_elements = self.get_realistic_verizon_dom_elements()
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
                
                # Score snippets with MarkupLM (detailed)
                scored_snippets = self.score_snippets_with_markuplm_detailed(html_snippets, step, match_elements)
                
                if not scored_snippets:
                    return {
                        "success": False,
                        "error": "Failed to score snippets with MarkupLM",
                        "step": step
                    }
                
                # Get the highest scoring element
                best_result = scored_snippets[0]
                
                print(f"\n🏆 Best match selected:")
                print(f"   Score: {best_result['score']:.6f}")
                print(f"   XPath: {best_result['xpath']}")
                print(f"   HTML snippet length: {len(best_result['snippet'])} chars")
                print(f"   Element: {best_result['element'].get('tagName', 'unknown')} (ID: {best_result['element'].get('attributes', {}).get('id', 'no-id')}) - '{best_result['element'].get('innerText', '')[:50]}...'")
                
                execution_time = time.time() - start_time
                
                return {
                    "success": True,
                    "step_type": "click",
                    "score": best_result['score'],
                    "xpath": best_result['xpath'],
                    "html_snippet": best_result['snippet'],
                    "execution_time": execution_time,
                    "step": step,
                    "target_text": target_text,
                    "best_element": best_result['element'],
                    "total_matches": len(match_elements),
                    "markup_input": best_result.get('markup_input', {}),
                    "markup_output": best_result.get('markup_output', {}),
                    "all_results": scored_snippets
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
    
    def run_realistic_verizon_test(self):
        """Run the realistic Verizon test."""
        print("🚀 Starting Realistic Verizon Test")
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
                # Execute step with detailed analysis
                result = self.execute_step_detailed(step, i)
                results.append(result)
                
                if result['success']:
                    print(f"\n✅ Step {i} completed successfully!")
                    print(f"   Step Type: {result.get('step_type', 'unknown')}")
                    if 'score' in result:
                        print(f"   Score: {result.get('score', 0):.6f}")
                    if 'xpath' in result:
                        print(f"   XPath: {result.get('xpath', 'N/A')}")
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
        
        return results


def run_realistic_verizon_dom_test():
    """Run the realistic Verizon DOM test."""
    print("🔍 Starting Realistic Verizon DOM Test")
    print("=" * 80)
    
    try:
        test = RealisticVerizonDOMTest()
        results = test.run_realistic_verizon_test()
        return results
    except Exception as e:
        print(f"❌ Test failed to initialize: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    run_realistic_verizon_dom_test()