"""
XPath generation utilities for HER framework.
Separated from Runner to avoid circular imports.
"""

from typing import Dict, Any


def generate_xpath_for_element(element: Dict[str, Any]) -> str:
    """Generate XPath only for top candidates to save processing time."""
    tag = (element.get('tag') or '').lower()
    attrs = element.get('attrs', {})
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