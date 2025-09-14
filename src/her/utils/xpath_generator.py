"""
XPath generation utilities for HER framework.
Separated from Runner to avoid circular imports.
"""

from typing import Dict, Any


def generate_xpath_for_element(element: Dict[str, Any]) -> str:
    """Generate RELATIVE XPath only for top candidates to save processing time.
    
    STRICT REQUIREMENT: All XPath selectors must be relative (start with //)
    Never generate absolute paths (starting with /html or /body)
    """
    tag = (element.get('tag') or '').lower()
    attrs = element.get('attrs', {}) or element.get('attributes', {})
    text = element.get('text', '').strip()
    
    if not tag or tag == '#text':
        return ''
    
    # STRICT VALIDATION: Ensure all selectors are relative
    def validate_relative_xpath(xpath: str) -> str:
        """Ensure XPath is relative and never absolute."""
        if not xpath:
            return ''
        
        # Remove any absolute paths and convert to relative
        if xpath.startswith('/html'):
            # Convert /html/body/div to //div
            xpath = '//' + xpath.split('/')[-1]
        elif xpath.startswith('/body'):
            # Convert /body/div to //div  
            xpath = '//' + xpath.split('/')[-1]
        elif xpath.startswith('/'):
            # Convert /div to //div
            xpath = '//' + xpath[1:]
        elif not xpath.startswith('//'):
            # Ensure it starts with //
            xpath = '//' + xpath
        
        return xpath
    
    # Priority order for XPath generation (ALL RELATIVE)
    if attrs.get('id'):
        xpath = f"//*[@id='{attrs['id']}']"
    elif attrs.get('data-testid'):
        xpath = f"//*[@data-testid='{attrs['data-testid']}']"
    elif attrs.get('aria-label'):
        xpath = f"//*[@aria-label='{attrs['aria-label']}']"
    elif attrs.get('name'):
        xpath = f"//{tag}[@name='{attrs['name']}']"
    elif attrs.get('class'):
        # Use first class for specificity
        first_class = attrs['class'].split()[0]
        xpath = f"//{tag}[contains(@class, '{first_class}')]"
    elif text and len(text) < 100:  # Avoid very long text
        # Escape quotes in text and use correct tag
        escaped_text = text.replace("'", "\\'").replace('"', '\\"')
        xpath = f"//{tag}[normalize-space()='{escaped_text}']"
    elif tag in ['textarea', 'input'] and attrs.get('placeholder'):
        # For form elements, use placeholder if available
        xpath = f"//{tag}[@placeholder='{attrs['placeholder']}']"
    elif tag in ['textarea', 'input'] and attrs.get('name'):
        # For form elements, use name attribute
        xpath = f"//{tag}[@name='{attrs['name']}']"
    elif attrs.get('title'):
        # Use title attribute as fallback
        xpath = f"//{tag}[@title='{attrs['title']}']"
    elif attrs.get('alt') and tag in ['img', 'input']:
        # Use alt attribute for images and inputs
        xpath = f"//{tag}[@alt='{attrs['alt']}']"
    elif attrs.get('href') and tag == 'a':
        # Use href for links
        xpath = f"//a[@href='{attrs['href']}']"
    elif attrs.get('type') and tag == 'input':
        # Use type attribute for inputs
        xpath = f"//input[@type='{attrs['type']}']"
    else:
        # Generic fallback with position - but still relative
        xpath = f"//{tag}"
    
    # STRICT VALIDATION: Ensure result is relative
    validated_xpath = validate_relative_xpath(xpath)
    
    # Final safety check - reject if somehow absolute
    if validated_xpath.startswith('/html') or validated_xpath.startswith('/body'):
        # Emergency fallback to simple relative selector
        validated_xpath = f"//{tag}"
    
    return validated_xpath