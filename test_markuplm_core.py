#!/usr/bin/env python3
"""
Test MarkupLM Core Functionality

This script tests the core MarkupLM functionality with real models
and demonstrates the exact workflow you described.
"""

import os
import sys
import time
import re
from typing import List, Dict, Any, Tuple

# Add src to path
sys.path.insert(0, '/workspace/src')

# Import real MarkupLM components (no mocking)
from transformers import MarkupLMProcessor, MarkupLMForQuestionAnswering
import torch


def test_markuplm_loading():
    """Test that MarkupLM model loads correctly."""
    print("🧪 Testing MarkupLM Model Loading")
    print("=" * 50)
    
    try:
        model_name = "microsoft/markuplm-base-finetuned-websrc"
        print(f"Loading model: {model_name}")
        
        processor = MarkupLMProcessor.from_pretrained(model_name)
        model = MarkupLMForQuestionAnswering.from_pretrained(model_name)
        model.eval()
        
        print("✅ MarkupLM model loaded successfully!")
        print(f"Model device: {next(model.parameters()).device}")
        print(f"Model config: {model.config.model_type}")
        
        return processor, model
        
    except Exception as e:
        print(f"❌ Failed to load MarkupLM model: {e}")
        raise


def extract_target_text(step: str) -> str:
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
    
    return ""


def find_exact_match_nodes(elements: List[Dict[str, Any]], target_text: str) -> List[Dict[str, Any]]:
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


def build_html_context(node: Dict[str, Any], all_elements: List[Dict[str, Any]]) -> str:
    """Build HTML context for a node including grandparent and siblings."""
    print(f"🏗️  Building HTML context for node: {node.get('tag', 'unknown')}")
    
    # Find parent elements (up to grandparent level)
    parents = find_parent_elements(node, all_elements)
    
    # Find sibling elements
    siblings = find_sibling_elements(node, all_elements, parents)
    
    # Build HTML structure
    html_parts = []
    
    # Add grandparent context
    for parent in parents[-2:]:  # Last 2 parents (parent + grandparent)
        tag = parent.get('tag', 'div')
        attrs = parent.get('attributes', {})
        attr_str = build_attribute_string(attrs)
        html_parts.append(f'<{tag}{attr_str}>')
    
    # Add sibling context
    if siblings:
        html_parts.append('<div class="sibling-context">')
        for sibling in siblings[:5]:  # Limit to 5 siblings
            tag = sibling.get('tag', 'span')
            text = sibling.get('text', '')[:50]  # Truncate long text
            attrs = sibling.get('attributes', {})
            attr_str = build_attribute_string(attrs)
            html_parts.append(f'<{tag}{attr_str}>{text}</{tag}>')
        html_parts.append('</div>')
    
    # Add target node
    tag = node.get('tag', 'div')
    text = node.get('text', '')
    attrs = node.get('attributes', {})
    attr_str = build_attribute_string(attrs)
    html_parts.append(f'<{tag}{attr_str}>{text}</{tag}>')
    
    # Close parent tags
    for parent in parents[-2:]:
        tag = parent.get('tag', 'div')
        html_parts.append(f'</{tag}>')
    
    html_context = ''.join(html_parts)
    print(f"   Built HTML context ({len(html_context)} chars)")
    return html_context


def find_parent_elements(node: Dict[str, Any], all_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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


def find_sibling_elements(node: Dict[str, Any], all_elements: List[Dict[str, Any]], 
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


def build_attribute_string(attrs: Dict[str, Any]) -> str:
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


def score_snippets_with_markuplm(processor, model, html_snippets: List[str], query: str) -> List[Tuple[float, str]]:
    """Score HTML snippets using real MarkupLM model."""
    print(f"🤖 Scoring {len(html_snippets)} snippets with MarkupLM")
    
    results = []
    
    for idx, snippet in enumerate(html_snippets):
        try:
            # Prepare inputs for MarkupLM
            inputs = processor(
                questions=query,
                html_strings=[snippet],
                return_tensors="pt"
            )
            
            # Get model predictions
            with torch.no_grad():
                outputs = model(**inputs)
                
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


def generate_best_xpath(node: Dict[str, Any]) -> str:
    """Generate the best XPath for a node."""
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
    else:
        xpath = f"//{tag}"
        print(f"   Using generic XPath: {xpath}")
        return xpath


def test_complete_workflow():
    """Test the complete workflow as described."""
    print("🚀 Testing Complete MarkupLM Workflow")
    print("=" * 80)
    
    # Load MarkupLM model
    processor, model = test_markuplm_loading()
    
    # Sample test data (simulating Verizon page elements)
    all_elements = [
        {
            "tag": "button",
            "text": "Apple",
            "attributes": {
                "id": "apple-filter-btn",
                "class": "filter-button active",
                "data-testid": "apple-filter",
                "aria-label": "Filter by Apple brand"
            },
            "visible": True,
            "xpath": "//div[@class='filter-container']/button[@id='apple-filter-btn']"
        },
        {
            "tag": "button",
            "text": "Samsung",
            "attributes": {
                "id": "samsung-filter-btn",
                "class": "filter-button",
                "data-testid": "samsung-filter"
            },
            "visible": True,
            "xpath": "//div[@class='filter-container']/button[@id='samsung-filter-btn']"
        },
        {
            "tag": "div",
            "text": "Filter Container",
            "attributes": {
                "class": "filter-container"
            },
            "visible": True,
            "xpath": "//div[@class='filter-container']"
        },
        {
            "tag": "a",
            "text": "Apple",
            "attributes": {
                "href": "/brands/apple",
                "class": "brand-link"
            },
            "visible": True,
            "xpath": "//a[@href='/brands/apple']"
        }
    ]
    
    # Test step
    step = 'Click on "Apple" filter'
    print(f"\n🔍 Testing step: {step}")
    
    # Step 1: Extract target text
    target_text = extract_target_text(step)
    print(f"Target text: '{target_text}'")
    
    # Step 2: Find exact match nodes
    match_nodes = find_exact_match_nodes(all_elements, target_text)
    
    if not match_nodes:
        print("❌ No exact match nodes found!")
        return
    
    # Step 3: Build HTML context for each node
    html_snippets = []
    for node in match_nodes:
        html_context = build_html_context(node, all_elements)
        html_snippets.append(html_context)
    
    # Step 4: Score snippets with MarkupLM
    scored_snippets = score_snippets_with_markuplm(processor, model, html_snippets, step)
    
    if not scored_snippets:
        print("❌ Failed to score snippets!")
        return
    
    # Step 5: Get highest scoring node and generate XPath
    best_score, best_html = scored_snippets[0]
    best_node = match_nodes[0]  # Assuming same order
    
    print(f"\n🏆 Best match:")
    print(f"   Score: {best_score:.3f}")
    print(f"   Node: {best_node.get('tag')} - {best_node.get('text')}")
    print(f"   HTML snippet length: {len(best_html)} chars")
    
    # Step 6: Generate best XPath
    best_xpath = generate_best_xpath(best_node)
    
    print(f"\n✅ Workflow completed successfully!")
    print(f"   Final XPath: {best_xpath}")
    print(f"   Ready for Playwright execution")
    
    return {
        "xpath": best_xpath,
        "score": best_score,
        "node": best_node,
        "html_snippet": best_html
    }


def main():
    """Main function."""
    try:
        result = test_complete_workflow()
        print(f"\n🎉 Test completed successfully!")
        return result
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()