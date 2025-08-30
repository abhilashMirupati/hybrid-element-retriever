# archived duplicate of src/her/locator/synthesize.py
"""Locator synthesis for generating robust selectors."""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from her.bridge.snapshot import DOMNode

logger = logging.getLogger(__name__)


@dataclass
class SynthesizedLocator:
    """Synthesized locator result."""
    selector: str
    strategy: str  # 'css', 'xpath', 'text', 'aria'
    confidence: float
    is_unique: bool
    alternatives: List[str]
    meta: Dict[str, any]
    

class LocatorSynthesizer:
    """Synthesizes robust locators from DOM nodes.
    
    Prioritizes:
    1. CSS selectors (stable, fast)
    2. Contextual XPath (when CSS insufficient)
    3. Text/ARIA fallbacks
    """
    
    def __init__(self):
        self.max_alternatives = 3
        
    def synthesize(
        self,
        node: DOMNode,
        context_nodes: Optional[List[DOMNode]] = None
    ) -> SynthesizedLocator:
        """Synthesize best locator for a node.
        
        Args:
            node: Target DOM node
            context_nodes: Other nodes in frame for uniqueness checking
            
        Returns:
            SynthesizedLocator with best selector
        """
        alternatives = []
        
        # Try CSS selector first
        css_selector = self._synthesize_css(node)
        if css_selector:
            is_unique = self._check_uniqueness(css_selector, 'css', node, context_nodes)
            confidence = self._calculate_css_confidence(css_selector, is_unique)
            
            if confidence > 0.7:  # High confidence CSS
                return SynthesizedLocator(
                    selector=css_selector,
                    strategy='css',
                    confidence=confidence,
                    is_unique=is_unique,
                    alternatives=self._generate_alternatives(node, exclude='css'),
                    meta={
                        'node_name': node.node_name,
                        'has_id': 'id' in node.attributes,
                        'depth': node.xpath.count('/')
                    }
                )
            alternatives.append(css_selector)
            
        # Try contextual XPath
        xpath_selector = self._synthesize_xpath(node, context_nodes)
        if xpath_selector:
            is_unique = self._check_uniqueness(xpath_selector, 'xpath', node, context_nodes)
            confidence = self._calculate_xpath_confidence(xpath_selector, is_unique)
            
            return SynthesizedLocator(
                selector=xpath_selector,
                strategy='xpath',
                confidence=confidence,
                is_unique=is_unique,
                alternatives=alternatives[:self.max_alternatives],
                meta={
                    'node_name': node.node_name,
                    'fallback_reason': 'css_not_unique' if css_selector else 'no_css',
                    'depth': node.xpath.count('/')
                }
            )
            
        # Last resort: use provided paths
        return SynthesizedLocator(
            selector=node.css_path if node.css_path else node.xpath,
            strategy='css' if node.css_path else 'xpath',
            confidence=0.3,
            is_unique=False,
            alternatives=alternatives[:self.max_alternatives],
            meta={
                'node_name': node.node_name,
                'fallback_reason': 'synthesis_failed'
            }
        )
        
    def _synthesize_css(self, node: DOMNode) -> Optional[str]:
        """Synthesize CSS selector for node.
        
        Args:
            node: Target node
            
        Returns:
            CSS selector or None
        """
        parts = []
        
        # Start with tag name
        tag = node.node_name.lower()
        if tag in ['#document', '#text', '#comment']:
            return None
            
        selector = tag
        
        # Add ID if present and not hash-like
        if 'id' in node.attributes:
            id_val = node.attributes['id']
            if id_val and not self._is_generated_id(id_val):
                return f"#{id_val}"  # ID alone is often sufficient
                
        # Add classes (limit to meaningful ones)
        if 'class' in node.attributes:
            classes = node.attributes['class'].split()
            meaningful_classes = [
                cls for cls in classes[:3]  # Limit number
                if not self._is_generated_class(cls)
            ]
            if meaningful_classes:
                selector += '.' + '.'.join(meaningful_classes)
                
        # Add key attributes
        for attr in ['type', 'name', 'role', 'aria-label']:
            if attr in node.attributes:
                value = node.attributes[attr]
                if value and len(value) < 50:  # Reasonable length
                    # Escape special characters
                    escaped = value.replace('"', '\\"')
                    selector += f'[{attr}="{escaped}"]'
                    break  # One attribute usually enough
                    
        # Add text content for buttons/links
        if tag in ['button', 'a'] and node.text_content:
            text = node.text_content.strip()[:30]
            if text and not any(c in text for c in ['\n', '\r', '\t']):
                # Use :contains pseudo-selector (jQuery-style, may need adjustment)
                selector = f"{selector}:contains('{text}')"
                
        return selector if selector != tag else None
        
    def _synthesize_xpath(self, node: DOMNode, context_nodes: Optional[List[DOMNode]]) -> str:
        """Synthesize contextual XPath for node.
        
        Args:
            node: Target node
            context_nodes: Context for uniqueness
            
        Returns:
            XPath selector
        """
        # Start with basic path
        if node.xpath:
            base_xpath = node.xpath
        else:
            base_xpath = f"//{node.node_name.lower()}"
            
        # Make more specific with attributes
        conditions = []
        
        # Add ID condition
        if 'id' in node.attributes and node.attributes['id']:
            conditions.append(f"@id='{node.attributes['id']}'")
            
        # Add class condition (partial match)
        if 'class' in node.attributes:
            classes = node.attributes['class'].split()
            for cls in classes[:2]:  # Limit classes
                if not self._is_generated_class(cls):
                    conditions.append(f"contains(@class, '{cls}')")
                    break
                    
        # Add text condition
        if node.text_content:
            text = node.text_content.strip()[:30]
            if text:
                # Escape quotes
                text = text.replace("'", "\\'") 
                conditions.append(f"contains(text(), '{text}')")
                
        # Add ARIA label
        if node.aria_label:
            conditions.append(f"@aria-label='{node.aria_label}'")
            
        # Build final XPath
        if conditions:
            condition_str = ' and '.join(conditions[:3])  # Limit conditions
            
            # Try to make it relative to a stable ancestor
            if context_nodes and len(context_nodes) > 10:
                # Find stable ancestor (e.g., form, main, nav)
                stable_ancestors = ['form', 'main', 'nav', 'section', 'article']
                for ancestor in stable_ancestors:
                    if ancestor in base_xpath:
                        # Make relative to ancestor
                        parts = base_xpath.split(f'/{ancestor}/')
                        if len(parts) > 1:
                            return f"//{ancestor}[1]//{node.node_name.lower()}[{condition_str}]"
                            
            return f"//{node.node_name.lower()}[{condition_str}]"
            
        return base_xpath
        
    def _check_uniqueness(
        self,
        selector: str,
        strategy: str,
        target_node: DOMNode,
        context_nodes: Optional[List[DOMNode]]
    ) -> bool:
        """Check if selector is unique in context.
        
        Args:
            selector: Selector to check
            strategy: Selector strategy
            target_node: Expected node
            context_nodes: Context nodes
            
        Returns:
            True if selector matches only target node
        """
        if not context_nodes:
            return True  # Assume unique if no context
            
        matches = 0
        
        if strategy == 'css':
            # Simplified CSS matching (would use proper CSS parser in production)
            for node in context_nodes:
                if self._matches_css(node, selector):
                    matches += 1
                    if matches > 1:
                        return False
                        
        elif strategy == 'xpath':
            # Simplified XPath matching
            for node in context_nodes:
                if self._matches_xpath(node, selector):
                    matches += 1
                    if matches > 1:
                        return False
                        
        return matches == 1
        
    def _matches_css(self, node: DOMNode, selector: str) -> bool:
        """Check if node matches CSS selector (simplified).
        
        Args:
            node: Node to check
            selector: CSS selector
            
        Returns:
            True if matches
        """
        # Very simplified CSS matching - in production would use proper parser
        
        # Check ID
        if selector.startswith('#'):
            id_match = re.match(r'^#([\w-]+)', selector)
            if id_match:
                return node.attributes.get('id') == id_match.group(1)
                
        # Check tag
        tag_match = re.match(r'^(\w+)', selector)
        if tag_match:
            if node.node_name.lower() != tag_match.group(1):
                return False
                
        # Check classes
        class_matches = re.findall(r'\.([\w-]+)', selector)
        if class_matches:
            node_classes = set(node.attributes.get('class', '').split())
            for required_class in class_matches:
                if required_class not in node_classes:
                    return False
                    
        # Check attributes
        attr_matches = re.findall(r'\[(\w+)=["\']([^"\']*)["\']]', selector)
        for attr_name, attr_value in attr_matches:
            if node.attributes.get(attr_name) != attr_value:
                return False
                
        return True
        
    def _matches_xpath(self, node: DOMNode, selector: str) -> bool:
        """Check if node matches XPath selector (simplified).
        
        Args:
            node: Node to check
            selector: XPath selector
            
        Returns:
            True if matches
        """
        # Very simplified XPath matching
        
        # Extract tag name from XPath
        tag_match = re.search(r'//?(\w+)', selector)
        if tag_match:
            if node.node_name.lower() != tag_match.group(1):
                return False
                
        # Check conditions
        if '[' in selector:
            # Extract conditions
            conditions = re.findall(r'\[([^]]+)\]', selector)
            for condition in conditions:
                # Check ID condition
                if '@id=' in condition:
                    id_match = re.search(r"@id='([^']+)'", condition)
                    if id_match and node.attributes.get('id') != id_match.group(1):
                        return False
                        
                # Check class contains
                if 'contains(@class' in condition:
                    class_match = re.search(r"contains\(@class,\s*'([^']+)'\)", condition)
                    if class_match:
                        required_class = class_match.group(1)
                        node_classes = node.attributes.get('class', '')
                        if required_class not in node_classes:
                            return False
                            
                # Check text contains
                if 'contains(text()' in condition:
                    text_match = re.search(r"contains\(text\(\),\s*'([^']+)'\)", condition)
                    if text_match:
                        required_text = text_match.group(1)
                        if not node.text_content or required_text not in node.text_content:
                            return False
                            
        return True
        
    def _calculate_css_confidence(self, selector: str, is_unique: bool) -> float:
        """Calculate confidence score for CSS selector.
        
        Args:
            selector: CSS selector
            is_unique: Whether selector is unique
            
        Returns:
            Confidence score [0, 1]
        """
        confidence = 0.5 if is_unique else 0.2
        
        # Bonus for ID
        if selector.startswith('#'):
            confidence += 0.3
            
        # Bonus for semantic tags
        semantic_tags = ['button', 'input', 'a', 'form', 'nav']
        if any(tag in selector for tag in semantic_tags):
            confidence += 0.1
            
        # Penalty for many classes
        class_count = selector.count('.')
        if class_count > 3:
            confidence -= 0.1
            
        # Penalty for complex selectors
        if len(selector) > 100:
            confidence -= 0.2
            
        return max(0.0, min(1.0, confidence))
        
    def _calculate_xpath_confidence(self, selector: str, is_unique: bool) -> float:
        """Calculate confidence score for XPath selector.
        
        Args:
            selector: XPath selector
            is_unique: Whether selector is unique
            
        Returns:
            Confidence score [0, 1]
        """
        confidence = 0.4 if is_unique else 0.1
        
        # Bonus for ID condition
        if '@id=' in selector:
            confidence += 0.2
            
        # Bonus for text content
        if 'text()' in selector:
            confidence += 0.1
            
        # Penalty for deep paths
        depth = selector.count('/')
        if depth > 5:
            confidence -= 0.1
            
        # Penalty for position indices
        if re.search(r'\[\d+\]', selector):
            confidence -= 0.2
            
        return max(0.0, min(1.0, confidence))
        
    def _is_generated_id(self, id_val: str) -> bool:
        """Check if ID appears to be generated/hash-like.
        
        Args:
            id_val: ID value
            
        Returns:
            True if likely generated
        """
        if not id_val or len(id_val) < 8:
            return False
            
        # Check for patterns
        patterns = [
            len(id_val) > 20,  # Very long
            re.match(r'^[a-f0-9]{8,}$', id_val.lower()),  # Hex string
            re.match(r'^\d{10,}$', id_val),  # Long number
            '-' in id_val and len(id_val) == 36,  # UUID-like
        ]
        
        return any(patterns)
        
    def _is_generated_class(self, class_val: str) -> bool:
        """Check if class appears to be generated.
        
        Args:
            class_val: Class value
            
        Returns:
            True if likely generated
        """
        if not class_val:
            return False
            
        # Check for patterns
        patterns = [
            len(class_val) > 15 and any(c.isdigit() for c in class_val),  # Long with numbers
            re.match(r'^[a-z]{2,6}-[a-f0-9]{4,}', class_val.lower()),  # Prefix-hash pattern
            '__' in class_val,  # BEM with hash
            class_val.startswith('css-') and len(class_val) > 10,  # CSS modules
        ]
        
        return any(patterns)
        
    def _generate_alternatives(self, node: DOMNode, exclude: str = '') -> List[str]:
        """Generate alternative selectors.
        
        Args:
            node: Target node
            exclude: Strategy to exclude
            
        Returns:
            List of alternative selectors
        """
        alternatives = []
        
        # Text-based selector
        if node.text_content and exclude != 'text':
            text = node.text_content.strip()[:30]
            if text:
                alternatives.append(f"text={text}")
                
        # ARIA-based selector
        if node.aria_label and exclude != 'aria':
            alternatives.append(f"aria-label={node.aria_label}")
            
        # Role-based selector
        if node.role and exclude != 'role':
            alternatives.append(f"role={node.role}")
            
        return alternatives[:self.max_alternatives]