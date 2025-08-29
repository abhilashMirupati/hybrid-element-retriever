"""Validators for edge cases and input sanitization."""

from typing import Any, Dict, List, Optional, Tuple
import re
import unicodedata
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class InputValidator:
    """Validates and sanitizes user inputs."""
    
    # XPath special characters that need escaping
    XPATH_SPECIAL_CHARS = r'["\']'
    
    # CSS selector special characters
    CSS_SPECIAL_CHARS = r'[#.\[\]():,>+~*^$|]'
    
    # Maximum reasonable lengths
    MAX_QUERY_LENGTH = 500
    MAX_XPATH_LENGTH = 1000
    MAX_URL_LENGTH = 2048
    
    @classmethod
    def validate_query(cls, query: str) -> Tuple[bool, str, Optional[str]]:
        """Validate and sanitize a user query.
        
        Args:
            query: User query string
            
        Returns:
            Tuple of (is_valid, sanitized_query, error_message)
        """
        # Handle None or non-string
        if query is None:
            return False, "", "Query cannot be None"
        
        if not isinstance(query, str):
            try:
                query = str(query)
            except Exception:
                return False, "", "Query must be a string"
        
        # Handle empty query
        query = query.strip()
        if not query:
            return False, "", "Query cannot be empty"
        
        # Check length
        if len(query) > cls.MAX_QUERY_LENGTH:
            return False, query[:cls.MAX_QUERY_LENGTH], f"Query too long (max {cls.MAX_QUERY_LENGTH} chars)"
        
        # Normalize unicode
        try:
            query = unicodedata.normalize('NFKC', query)
        except Exception as e:
            logger.warning(f"Unicode normalization failed: {e}")
        
        # Remove control characters
        query = ''.join(char for char in query if not unicodedata.category(char).startswith('C'))
        
        # Handle special characters (don't remove, just validate)
        if not query:
            return False, "", "Query contains only control characters"
        
        return True, query, None
    
    @classmethod
    def validate_xpath(cls, xpath: str) -> Tuple[bool, str, Optional[str]]:
        """Validate an XPath expression.
        
        Args:
            xpath: XPath expression
            
        Returns:
            Tuple of (is_valid, sanitized_xpath, error_message)
        """
        if not xpath or not isinstance(xpath, str):
            return False, "", "XPath must be a non-empty string"
        
        xpath = xpath.strip()
        
        # Check length
        if len(xpath) > cls.MAX_XPATH_LENGTH:
            return False, "", f"XPath too long (max {cls.MAX_XPATH_LENGTH} chars)"
        
        # Basic syntax validation
        try:
            # Check for balanced brackets
            if xpath.count('[') != xpath.count(']'):
                return False, "", "Unbalanced brackets in XPath"
            
            # Check for balanced parentheses
            if xpath.count('(') != xpath.count(')'):
                return False, "", "Unbalanced parentheses in XPath"
            
            # Check for balanced quotes
            single_quotes = xpath.count("'")
            double_quotes = xpath.count('"')
            if single_quotes % 2 != 0 and double_quotes % 2 != 0:
                return False, "", "Unbalanced quotes in XPath"
            
            # Validate starts with / or //
            if not xpath.startswith('/') and not xpath.startswith('('):
                return False, "", "XPath must start with / or //"
            
        except Exception as e:
            return False, "", f"XPath validation error: {e}"
        
        return True, xpath, None
    
    @classmethod
    def validate_url(cls, url: str) -> Tuple[bool, str, Optional[str]]:
        """Validate a URL.
        
        Args:
            url: URL string
            
        Returns:
            Tuple of (is_valid, sanitized_url, error_message)
        """
        if not url or not isinstance(url, str):
            return False, "", "URL must be a non-empty string"
        
        url = url.strip()
        
        # Check length
        if len(url) > cls.MAX_URL_LENGTH:
            return False, "", f"URL too long (max {cls.MAX_URL_LENGTH} chars)"
        
        # Parse URL
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in ('http', 'https', 'file', ''):
                return False, "", f"Invalid URL scheme: {parsed.scheme}"
            
            # Add scheme if missing
            if not parsed.scheme:
                url = f"https://{url}"
                parsed = urlparse(url)
            
            # Check for valid netloc
            if not parsed.netloc and parsed.scheme in ('http', 'https'):
                return False, "", "Invalid URL: missing domain"
            
        except Exception as e:
            return False, "", f"URL parsing error: {e}"
        
        return True, url, None
    
    @classmethod
    def escape_xpath_string(cls, text: str) -> str:
        """Escape a string for use in XPath expressions.
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text safe for XPath
        """
        if '"' not in text:
            return f'"{text}"'
        elif "'" not in text:
            return f"'{text}'"
        else:
            # Use concat for mixed quotes
            parts = []
            for char in text:
                if char == '"':
                    parts.append("'\"'")
                elif char == "'":
                    parts.append('"' + "'" + '"')
                else:
                    if parts and not parts[-1].startswith('concat'):
                        parts[-1] = parts[-1][:-1] + char + parts[-1][-1]
                    else:
                        parts.append(f'"{char}"')
            
            return f"concat({','.join(parts)})"
    
    @classmethod
    def escape_css_selector(cls, text: str) -> str:
        """Escape a string for use in CSS selectors.
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text safe for CSS
        """
        # Escape special characters
        escaped = re.sub(cls.CSS_SPECIAL_CHARS, r'\\\g<0>', text)
        return escaped


class DOMValidator:
    """Validates DOM-related operations."""
    
    @classmethod
    def validate_element_descriptor(cls, descriptor: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate an element descriptor.
        
        Args:
            descriptor: Element descriptor dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not descriptor:
            return False, "Descriptor cannot be empty"
        
        if not isinstance(descriptor, dict):
            return False, "Descriptor must be a dictionary"
        
        # Check for at least one identifying property
        identifying_props = ['id', 'tag', 'tagName', 'text', 'xpath', 'selector']
        if not any(prop in descriptor for prop in identifying_props):
            return False, "Descriptor must have at least one identifying property"
        
        # Validate tag name if present
        tag = descriptor.get('tag') or descriptor.get('tagName')
        if tag and not cls._is_valid_tag_name(tag):
            return False, f"Invalid tag name: {tag}"
        
        return True, None
    
    @classmethod
    def _is_valid_tag_name(cls, tag: str) -> bool:
        """Check if tag name is valid."""
        if not tag or not isinstance(tag, str):
            return False
        
        # Allow wildcard
        if tag == '*':
            return True
        
        # Check for valid HTML tag pattern
        return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9-]*$', tag))
    
    @classmethod
    def handle_duplicate_elements(cls, descriptors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Handle duplicate elements in descriptors.
        
        Args:
            descriptors: List of element descriptors
            
        Returns:
            Deduplicated list with unique identifiers
        """
        seen = set()
        unique_descriptors = []
        
        for desc in descriptors:
            # Create a unique key
            key_parts = []
            
            # Use multiple attributes for uniqueness
            for attr in ['tag', 'id', 'text', 'xpath']:
                if attr in desc:
                    key_parts.append(f"{attr}:{desc[attr]}")
            
            if not key_parts:
                # Use all attributes if no standard ones
                key_parts = [f"{k}:{v}" for k, v in desc.items()]
            
            key = "|".join(key_parts)
            
            if key not in seen:
                seen.add(key)
                unique_descriptors.append(desc)
            else:
                # Add index to make unique
                index = 1
                while f"{key}|{index}" in seen:
                    index += 1
                
                desc_copy = desc.copy()
                desc_copy['_duplicate_index'] = index
                unique_descriptors.append(desc_copy)
                seen.add(f"{key}|{index}")
        
        return unique_descriptors
    
    @classmethod
    def validate_dom_size(cls, descriptors: List[Dict[str, Any]], max_nodes: int = 10000) -> Tuple[bool, Optional[str]]:
        """Validate DOM size is within reasonable limits.
        
        Args:
            descriptors: List of element descriptors
            max_nodes: Maximum number of nodes
            
        Returns:
            Tuple of (is_valid, warning_message)
        """
        if not descriptors:
            return True, None
        
        num_nodes = len(descriptors)
        
        if num_nodes > max_nodes:
            return False, f"DOM too large: {num_nodes} nodes (max {max_nodes})"
        
        if num_nodes > max_nodes * 0.8:
            return True, f"Large DOM warning: {num_nodes} nodes approaching limit"
        
        return True, None


class FormValidator:
    """Validates form-related operations."""
    
    @classmethod
    def validate_form_input(cls, input_type: str, value: Any) -> Tuple[bool, Any, Optional[str]]:
        """Validate form input value based on type.
        
        Args:
            input_type: HTML input type
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, sanitized_value, error_message)
        """
        if input_type == "email":
            return cls._validate_email(value)
        elif input_type == "url":
            return cls._validate_url_input(value)
        elif input_type == "tel":
            return cls._validate_phone(value)
        elif input_type == "number":
            return cls._validate_number(value)
        elif input_type == "date":
            return cls._validate_date(value)
        elif input_type == "file":
            return cls._validate_file_path(value)
        else:
            # Default text validation
            return cls._validate_text(value)
    
    @classmethod
    def _validate_email(cls, email: Any) -> Tuple[bool, str, Optional[str]]:
        """Validate email address."""
        if not email:
            return False, "", "Email cannot be empty"
        
        email = str(email).strip()
        
        # Basic email regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, email, "Invalid email format"
        
        return True, email, None
    
    @classmethod
    def _validate_url_input(cls, url: Any) -> Tuple[bool, str, Optional[str]]:
        """Validate URL input."""
        return InputValidator.validate_url(str(url) if url else "")
    
    @classmethod
    def _validate_phone(cls, phone: Any) -> Tuple[bool, str, Optional[str]]:
        """Validate phone number."""
        if not phone:
            return False, "", "Phone cannot be empty"
        
        phone = str(phone).strip()
        
        # Remove common formatting
        phone_digits = re.sub(r'[^\d+]', '', phone)
        
        # Check for reasonable length
        if len(phone_digits) < 7 or len(phone_digits) > 15:
            return False, phone, "Invalid phone number length"
        
        return True, phone, None
    
    @classmethod
    def _validate_number(cls, value: Any) -> Tuple[bool, float, Optional[str]]:
        """Validate numeric input."""
        try:
            num = float(value)
            return True, num, None
        except (ValueError, TypeError):
            return False, 0.0, "Invalid number format"
    
    @classmethod
    def _validate_date(cls, date: Any) -> Tuple[bool, str, Optional[str]]:
        """Validate date input."""
        if not date:
            return False, "", "Date cannot be empty"
        
        date = str(date).strip()
        
        # Check common date formats
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
            r'^\d{2}-\d{2}-\d{4}$',  # DD-MM-YYYY
        ]
        
        for pattern in date_patterns:
            if re.match(pattern, date):
                return True, date, None
        
        return False, date, "Invalid date format"
    
    @classmethod
    def _validate_file_path(cls, path: Any) -> Tuple[bool, str, Optional[str]]:
        """Validate file path."""
        if not path:
            return False, "", "File path cannot be empty"
        
        path = str(path).strip()
        
        # Check for path traversal attempts
        if '..' in path or path.startswith('/'):
            return False, path, "Invalid file path"
        
        return True, path, None
    
    @classmethod
    def _validate_text(cls, text: Any) -> Tuple[bool, str, Optional[str]]:
        """Validate general text input."""
        if text is None:
            return True, "", None
        
        text = str(text)
        
        # Remove control characters
        text = ''.join(char for char in text if not unicodedata.category(char).startswith('C'))
        
        return True, text, None


class AccessibilityValidator:
    """Validates accessibility-related operations."""
    
    @classmethod
    def validate_aria_attributes(cls, attributes: Dict[str, str]) -> List[str]:
        """Validate ARIA attributes.
        
        Args:
            attributes: Dictionary of attributes
            
        Returns:
            List of validation warnings
        """
        warnings = []
        
        # Check for aria-label or aria-labelledby
        if not attributes.get('aria-label') and not attributes.get('aria-labelledby'):
            if attributes.get('role') in ['button', 'link', 'textbox']:
                warnings.append("Interactive element missing aria-label")
        
        # Check for valid roles
        role = attributes.get('role')
        if role:
            valid_roles = [
                'button', 'link', 'textbox', 'checkbox', 'radio',
                'menu', 'menuitem', 'tab', 'tabpanel', 'dialog',
                'alert', 'navigation', 'main', 'complementary'
            ]
            if role not in valid_roles:
                warnings.append(f"Unknown ARIA role: {role}")
        
        return warnings
    
    @classmethod
    def validate_language_support(cls, text: str) -> Dict[str, Any]:
        """Validate language and internationalization support.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with language info
        """
        info = {
            'has_rtl': False,
            'has_cjk': False,
            'has_emoji': False,
            'scripts': set()
        }
        
        for char in text:
            # Check for RTL characters
            if unicodedata.bidirectional(char) in ['R', 'AL']:
                info['has_rtl'] = True
            
            # Check for CJK
            if any(start <= ord(char) <= end for start, end in [
                (0x4E00, 0x9FFF),  # CJK Unified Ideographs
                (0x3040, 0x309F),  # Hiragana
                (0x30A0, 0x30FF),  # Katakana
                (0xAC00, 0xD7AF),  # Hangul
            ]):
                info['has_cjk'] = True
            
            # Check for emoji
            if unicodedata.category(char) == 'So':
                info['has_emoji'] = True
            
            # Track script
            info['scripts'].add(unicodedata.name(char, '').split()[0] if char.strip() else 'UNKNOWN')
        
        info['scripts'] = list(info['scripts'])
        return info