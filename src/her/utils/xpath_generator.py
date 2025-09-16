"""
XPath generation utilities for HER framework.
Enhanced for MarkupLM integration with hierarchical context support.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class XPathCandidate:
    """XPath candidate with metadata."""
    xpath: str
    element: Dict[str, Any]
    confidence: float
    strategy: str
    is_valid: bool = False
    validation_error: Optional[str] = None


def generate_xpath_for_element(element: Dict[str, Any]) -> str:
    """Generate XPath only for top candidates to save processing time."""
    tag = (element.get('tag') or '').lower()
    attrs = element.get('attrs', {}) or element.get('attributes', {})
    text = element.get('text', '').strip()
    
    if not tag or tag == '#text':
        return ''
    
    # Priority order for XPath generation
    if attrs.get('id'):
        return f"//*[@id='{attrs['id']}']"
    elif attrs.get('data-testid'):
        return f"//*[@data-testid='{attrs['data-testid']}']"
    elif attrs.get('aria-label'):
        return f"//*[@aria-label='{attrs['aria-label']}']"
    elif attrs.get('name'):
        return f"//{tag}[@name='{attrs['name']}']"
    elif attrs.get('class'):
        # Use first class for specificity
        first_class = attrs['class'].split()[0]
        return f"//{tag}[@class='{first_class}']"
    elif text and len(text) < 100:  # Avoid very long text
        # Escape quotes in text and use correct tag
        escaped_text = text.replace("'", "\\'").replace('"', '\\"')
        return f"//{tag}[normalize-space()='{escaped_text}']"
    elif tag in ['textarea', 'input'] and attrs.get('placeholder'):
        # For form elements, use placeholder if available
        return f"//{tag}[@placeholder='{attrs['placeholder']}']"
    elif tag in ['textarea', 'input'] and attrs.get('name'):
        # For form elements, use name attribute
        return f"//{tag}[@name='{attrs['name']}']"
    else:
        # Generic fallback with position
        return f"//{tag}"


def generate_xpath_candidates(element: Dict[str, Any], 
                             hierarchy_context: Optional[Dict[str, Any]] = None) -> List[XPathCandidate]:
    """Generate multiple XPath candidates for an element with hierarchical context.
    
    Args:
        element: Target element
        hierarchy_context: Optional hierarchical context
        
    Returns:
        List of XPath candidates
    """
    candidates = []
    tag = (element.get('tag') or '').lower()
    attrs = element.get('attrs', {}) or element.get('attributes', {})
    text = element.get('text', '').strip()
    
    if not tag or tag == '#text':
        return candidates
    
    # Strategy 1: ID-based XPath (highest priority)
    if attrs.get('id'):
        xpath = f"//*[@id='{attrs['id']}']"
        candidates.append(XPathCandidate(
            xpath=xpath,
            element=element,
            confidence=1.0,
            strategy="id_based"
        ))
    
    # Strategy 2: Data-testid-based XPath
    if attrs.get('data-testid'):
        xpath = f"//*[@data-testid='{attrs['data-testid']}']"
        candidates.append(XPathCandidate(
            xpath=xpath,
            element=element,
            confidence=0.95,
            strategy="testid_based"
        ))
    
    # Strategy 3: Aria-label-based XPath
    if attrs.get('aria-label'):
        xpath = f"//*[@aria-label='{attrs['aria-label']}']"
        candidates.append(XPathCandidate(
            xpath=xpath,
            element=element,
            confidence=0.9,
            strategy="aria_label_based"
        ))
    
    # Strategy 4: Name attribute XPath
    if attrs.get('name'):
        xpath = f"//{tag}[@name='{attrs['name']}']"
        candidates.append(XPathCandidate(
            xpath=xpath,
            element=element,
            confidence=0.85,
            strategy="name_based"
        ))
    
    # Strategy 5: Class-based XPath
    if attrs.get('class'):
        first_class = attrs['class'].split()[0]
        xpath = f"//{tag}[@class='{first_class}']"
        candidates.append(XPathCandidate(
            xpath=xpath,
            element=element,
            confidence=0.7,
            strategy="class_based"
        ))
    
    # Strategy 6: Text-based XPath
    if text and len(text) < 100:
        escaped_text = text.replace("'", "\\'").replace('"', '\\"')
        xpath = f"//{tag}[normalize-space()='{escaped_text}']"
        candidates.append(XPathCandidate(
            xpath=xpath,
            element=element,
            confidence=0.8,
            strategy="text_based"
        ))
    
    # Strategy 7: Hierarchical XPath (if context available)
    if hierarchy_context:
        hierarchical_xpath = generate_hierarchical_xpath(element, hierarchy_context)
        if hierarchical_xpath:
            candidates.append(XPathCandidate(
                xpath=hierarchical_xpath,
                element=element,
                confidence=0.75,
                strategy="hierarchical"
            ))
    
    # Strategy 8: Combined attribute XPath
    combined_xpath = generate_combined_xpath(element)
    if combined_xpath:
        candidates.append(XPathCandidate(
            xpath=combined_xpath,
            element=element,
            confidence=0.6,
            strategy="combined_attributes"
        ))
    
    # Strategy 9: Generic fallback
    candidates.append(XPathCandidate(
        xpath=f"//{tag}",
        element=element,
        confidence=0.3,
        strategy="generic_fallback"
    ))
    
    return candidates


def generate_hierarchical_xpath(element: Dict[str, Any], 
                               hierarchy_context: Dict[str, Any]) -> Optional[str]:
    """Generate XPath using hierarchical context.
    
    Args:
        element: Target element
        hierarchy_context: Hierarchical context
        
    Returns:
        Hierarchical XPath or None
    """
    hierarchy_path = hierarchy_context.get('hierarchy_path', [])
    if not hierarchy_path:
        return None
    
    # Build XPath from hierarchy path
    xpath_parts = []
    for level in hierarchy_path[-3:]:  # Use last 3 levels
        if ':' in level:
            tag, position = level.split(':')
            xpath_parts.append(f'{tag}[{position}]')
        else:
            xpath_parts.append(level)
    
    if xpath_parts:
        return '//' + '/'.join(xpath_parts)
    
    return None


def generate_combined_xpath(element: Dict[str, Any]) -> Optional[str]:
    """Generate XPath combining multiple attributes.
    
    Args:
        element: Target element
        
    Returns:
        Combined XPath or None
    """
    tag = (element.get('tag') or '').lower()
    attrs = element.get('attrs', {}) or element.get('attributes', {})
    text = element.get('text', '').strip()
    
    if not tag:
        return None
    
    conditions = []
    
    # Add class condition
    if attrs.get('class'):
        first_class = attrs['class'].split()[0]
        conditions.append(f'@class="{first_class}"')
    
    # Add text condition
    if text and len(text) < 50:  # Shorter text for combined XPath
        escaped_text = text.replace("'", "\\'").replace('"', '\\"')
        conditions.append(f'normalize-space()="{escaped_text}"')
    
    # Add type condition for form elements
    if tag in ['input', 'select', 'textarea'] and attrs.get('type'):
        conditions.append(f'@type="{attrs["type"]}"')
    
    if conditions:
        return f'//{tag}[{" and ".join(conditions)}]'
    
    return None


def validate_xpath_candidates(candidates: List[XPathCandidate], 
                            page=None) -> List[XPathCandidate]:
    """Validate XPath candidates using page object.
    
    Args:
        candidates: List of XPath candidates
        page: Optional page object for validation
        
    Returns:
        List of validated candidates
    """
    if not page:
        # If no page available, mark all as potentially valid
        for candidate in candidates:
            candidate.is_valid = True
        return candidates
    
    validated_candidates = []
    
    for candidate in candidates:
        try:
            # Use Playwright's locator to check if element exists
            elements = page.locator(candidate.xpath)
            count = elements.count()
            
            if count > 0:
                candidate.is_valid = True
                validated_candidates.append(candidate)
            else:
                candidate.is_valid = False
                candidate.validation_error = "Element not found in DOM"
                
        except Exception as e:
            candidate.is_valid = False
            candidate.validation_error = str(e)
    
    return validated_candidates


def select_best_xpath_candidate(candidates: List[XPathCandidate]) -> Optional[XPathCandidate]:
    """Select the best XPath candidate from validated candidates.
    
    Args:
        candidates: List of XPath candidates
        
    Returns:
        Best candidate or None
    """
    if not candidates:
        return None
    
    # Filter to only valid candidates
    valid_candidates = [c for c in candidates if c.is_valid]
    if not valid_candidates:
        return None
    
    # Sort by confidence (highest first)
    valid_candidates.sort(key=lambda c: c.confidence, reverse=True)
    
    return valid_candidates[0]