"""Mock HER client for functional validation testing"""

import json
import time
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path


class MockHERClient:
    """Simplified mock client for testing validation runner"""
    
    def __init__(self):
        self.cache = {}
        self.page = None
        
    async def initialize(self, page):
        """Initialize with playwright page"""
        self.page = page
        
    def clear_cache(self):
        """Clear the cache"""
        self.cache.clear()
        
    async def query(self, query: str) -> Dict[str, Any]:
        """Mock query implementation with basic scoring"""
        if not self.page:
            raise RuntimeError("Client not initialized")
            
        # Get page content
        content = await self.page.content()
        
        # Simple hash for cache key
        cache_key = hashlib.md5(f"{query}:{content[:100]}".encode()).hexdigest()
        
        # Check cache
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        # Simulate processing time
        time.sleep(0.1)  # Cold start latency
        
        # Mock scoring based on query keywords
        result = await self._mock_score(query, content)
        
        # Cache result
        self.cache[cache_key] = result
        return result
        
    async def _mock_score(self, query: str, content: str) -> Dict[str, Any]:
        """Mock scoring logic"""
        query_lower = query.lower()
        
        # Product disambiguation
        if "phone" in query_lower:
            if "iphone" in query_lower:
                return {
                    "xpath": "//div[@data-product-id='iphone-14']//button",
                    "css": "div[data-product-id='iphone-14'] button",
                    "strategy": "css",
                    "confidence": 0.92,
                    "element": {"text": "Add to Cart", "type": "button"}
                }
            else:
                return {
                    "xpath": "//button[@data-product-type='phone']",
                    "css": "button[data-product-type='phone']",
                    "strategy": "css",
                    "confidence": 0.88,
                    "element": {"text": "Add to Cart", "type": "button"}
                }
                
        elif "laptop" in query_lower:
            return {
                "xpath": "//button[@data-product-type='laptop']",
                "css": "button[data-product-type='laptop']",
                "strategy": "css",
                "confidence": 0.89,
                "element": {"text": "Add to Cart", "type": "button"}
            }
            
        elif "tablet" in query_lower:
            return {
                "xpath": "//div[@data-product-id='ipad-pro']//button",
                "css": "div[data-product-id='ipad-pro'] button",
                "strategy": "css",
                "confidence": 0.87,
                "element": {"text": "Add to Cart", "type": "button"}
            }
            
        # Form field disambiguation
        elif "email" in query_lower:
            return {
                "xpath": "//input[@type='email']",
                "css": "input[type='email']",
                "strategy": "css",
                "confidence": 0.96,
                "element": {"type": "email", "id": "email"}
            }
            
        elif "username" in query_lower:
            return {
                "xpath": "//input[@id='username']",
                "css": "input#username",
                "strategy": "css",
                "confidence": 0.95,
                "element": {"type": "text", "id": "username"}
            }
            
        elif "password" in query_lower:
            return {
                "xpath": "//input[@type='password'][@id='password']",
                "css": "input[type='password']#password",
                "strategy": "css",
                "confidence": 0.94,
                "element": {"type": "password", "id": "password"}
            }
            
        elif "submit" in query_lower:
            return {
                "xpath": "//button[@id='submit-active']",
                "css": "button#submit-active",
                "strategy": "css",
                "confidence": 0.91,
                "element": {"type": "submit", "text": "Create Account"}
            }
            
        # Default fallback
        return {
            "xpath": "//button",
            "css": "button",
            "strategy": "css",
            "confidence": 0.50,
            "element": {"text": "Unknown"}
        }
        
    async def act(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Mock action execution"""
        return {
            "success": True,
            "action": step.get("action", "click"),
            "post_action": {
                "dom_mutated": True,
                "url_changed": False
            }
        }