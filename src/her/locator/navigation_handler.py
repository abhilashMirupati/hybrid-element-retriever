"""
Navigation Handler for No-Semantic Mode

This module provides navigation handling functionality:
1. Separate navigation from element selection
2. Use page.goto(url) for navigation queries
3. Detect navigation vs element selection queries
4. Handle URL extraction from queries
"""

from __future__ import annotations

import re
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from .intent_parser import ParsedIntent

log = logging.getLogger("her.navigation_handler")

@dataclass
class NavigationResult:
    """Result of navigation operation."""
    success: bool
    url: Optional[str] = None
    status: Optional[int] = None
    error: Optional[str] = None
    strategy: str = "navigation"

class NavigationHandler:
    """Handler for navigation operations in no-semantic mode."""
    
    def __init__(self):
        self.domain_mapping = {
            'verizon': 'https://verizon.com',
            'google': 'https://google.com',
            'amazon': 'https://amazon.com',
            'facebook': 'https://facebook.com',
            'twitter': 'https://twitter.com',
            'linkedin': 'https://linkedin.com',
            'github': 'https://github.com',
            'stackoverflow': 'https://stackoverflow.com',
            'youtube': 'https://youtube.com',
            'netflix': 'https://netflix.com',
            'spotify': 'https://spotify.com',
            'instagram': 'https://instagram.com'
        }
    
    def is_navigation_query(self, parsed_intent: ParsedIntent) -> bool:
        """Check if query is a navigation request."""
        navigation_keywords = ['navigate', 'go to', 'visit', 'open', 'load', 'browse']
        query_lower = parsed_intent.original_step.lower()
        
        for keyword in navigation_keywords:
            if keyword in query_lower:
                return True
        
        # Check if target text looks like a URL
        target = parsed_intent.target_text
        if target and ('http' in target or 'www.' in target or target.endswith('.com')):
            return True
        
        return False
    
    def handle_navigation(self, parsed_intent: ParsedIntent, page) -> NavigationResult:
        """Handle navigation queries using page.goto()."""
        if not page:
            return NavigationResult(
                success=False,
                error='No page object available for navigation'
            )
        
        # Extract URL from target text or original step
        url = self._extract_url(parsed_intent)
        if not url:
            return NavigationResult(
                success=False,
                error='Could not extract URL from query'
            )
        
        try:
            # Use page.goto() for navigation
            response = page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            if response and response.status < 400:
                return NavigationResult(
                    success=True,
                    url=url,
                    status=response.status
                )
            else:
                return NavigationResult(
                    success=False,
                    url=url,
                    status=response.status if response else None,
                    error=f'Navigation failed with status: {response.status if response else "No response"}'
                )
        except Exception as e:
            return NavigationResult(
                success=False,
                url=url,
                error=f'Navigation error: {str(e)}'
            )
    
    def _extract_url(self, parsed_intent: ParsedIntent) -> Optional[str]:
        """Extract URL from parsed intent."""
        # Try target text first
        target = parsed_intent.target_text
        if target and ('http' in target or 'www.' in target):
            if not target.startswith('http'):
                target = 'https://' + target
            return target
        
        # Try original step
        step = parsed_intent.original_step
        url_pattern = r'https?://[^\s"\']+|www\.[^\s"\']+'
        match = re.search(url_pattern, step)
        if match:
            url = match.group(0)
            if not url.startswith('http'):
                url = 'https://' + url
            return url
        
        # Try to construct URL from target text using domain mapping
        if target:
            target_lower = target.lower().strip()
            
            # Check domain mapping first
            if target_lower in self.domain_mapping:
                return self.domain_mapping[target_lower]
            
            # Try to construct URL from target
            if target_lower.replace(' ', '').isalnum():
                return f'https://{target_lower.replace(" ", "").lower()}.com'
        
        return None
    
    def create_navigation_result(self, nav_result: NavigationResult) -> Dict[str, Any]:
        """Create standardized result for navigation."""
        if nav_result.success:
            return {
                'xpath': None,
                'element': None,
                'confidence': 1.0,
                'strategy': 'navigation-success',
                'url': nav_result.url,
                'status': nav_result.status
            }
        else:
            return {
                'xpath': None,
                'element': None,
                'confidence': 0.0,
                'strategy': 'navigation-failed',
                'error': nav_result.error,
                'url': nav_result.url
            }