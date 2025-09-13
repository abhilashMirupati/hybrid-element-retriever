"""
Intelligent snapshot caching system for HER framework.
Reduces duplicate snapshots and improves performance.
"""

import hashlib
import time
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class SnapshotCache:
    """Cache entry for page snapshots."""
    snapshot: Dict[str, Any]
    timestamp: float
    url_hash: str
    dom_hash: str
    element_count: int

class IntelligentSnapshotManager:
    """
    Manages snapshots intelligently to avoid duplicates and optimize performance.
    """
    
    def __init__(self, cache_ttl: float = 5.0, similarity_threshold: float = 0.95):
        """
        Initialize snapshot manager.
        
        Args:
            cache_ttl: Cache time-to-live in seconds
            similarity_threshold: Threshold for considering snapshots similar
        """
        self.cache: Dict[str, SnapshotCache] = {}
        self.cache_ttl = cache_ttl
        self.similarity_threshold = similarity_threshold
        self.last_snapshot_time = 0
        self.snapshot_cooldown = 0.5  # Minimum 500ms between snapshots
        
    def should_take_snapshot(self, 
                           current_url: str, 
                           force: bool = False,
                           action_type: str = "unknown") -> Tuple[bool, str]:
        """
        Determine if a new snapshot should be taken.
        
        Args:
            current_url: Current page URL
            force: Force snapshot regardless of cache
            action_type: Type of action being performed
            
        Returns:
            Tuple of (should_take, reason)
        """
        current_time = time.time()
        
        # Force snapshot if requested
        if force:
            return True, "forced"
            
        # Check cooldown period
        if current_time - self.last_snapshot_time < self.snapshot_cooldown:
            return False, f"cooldown ({self.snapshot_cooldown}s)"
            
        # Generate cache key
        cache_key = self._generate_cache_key(current_url)
        
        # Check if we have a valid cached snapshot
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            age = current_time - cached.timestamp
            
            if age < self.cache_ttl:
                return False, f"cached (age: {age:.1f}s)"
                
        # Determine based on action type
        if action_type in ["navigate", "page_transition"]:
            return True, "navigation"
        elif action_type in ["click", "type", "submit"]:
            return True, "interactive_action"
        elif action_type in ["wait", "scroll"]:
            return False, "non_interactive"
            
        return True, "default"
    
    def get_cached_snapshot(self, current_url: str) -> Optional[Dict[str, Any]]:
        """Get cached snapshot if available and valid."""
        cache_key = self._generate_cache_key(current_url)
        
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            age = time.time() - cached.timestamp
            
            if age < self.cache_ttl:
                return cached.snapshot
                
        return None
    
    def cache_snapshot(self, 
                      current_url: str, 
                      snapshot: Dict[str, Any]) -> None:
        """Cache a snapshot for future use."""
        current_time = time.time()
        cache_key = self._generate_cache_key(current_url)
        
        # Extract metadata
        dom_hash = snapshot.get('dom_hash', '')
        element_count = len(snapshot.get('elements', []))
        
        # Create cache entry
        self.cache[cache_key] = SnapshotCache(
            snapshot=snapshot,
            timestamp=current_time,
            url_hash=cache_key,
            dom_hash=dom_hash,
            element_count=element_count
        )
        
        self.last_snapshot_time = current_time
        
        # Clean up old cache entries
        self._cleanup_cache()
    
    def detect_page_changes(self, 
                           old_snapshot: Dict[str, Any], 
                           new_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect changes between snapshots.
        
        Returns:
            Dictionary with change information
        """
        old_elements = old_snapshot.get('elements', [])
        new_elements = new_snapshot.get('elements', [])
        
        old_count = len(old_elements)
        new_count = len(new_elements)
        
        # Simple change detection
        changes = {
            'element_count_change': new_count - old_count,
            'percentage_change': abs(new_count - old_count) / max(old_count, 1) * 100,
            'significant_change': abs(new_count - old_count) > 10,
            'url_changed': old_snapshot.get('url') != new_snapshot.get('url'),
            'dom_hash_changed': old_snapshot.get('dom_hash') != new_snapshot.get('dom_hash')
        }
        
        return changes
    
    def _generate_cache_key(self, url: str) -> str:
        """Generate cache key for URL."""
        return hashlib.md5(url.encode()).hexdigest()[:16]
    
    def _cleanup_cache(self) -> None:
        """Remove expired cache entries."""
        current_time = time.time()
        expired_keys = [
            key for key, cached in self.cache.items()
            if current_time - cached.timestamp > self.cache_ttl * 2
        ]
        
        for key in expired_keys:
            del self.cache[key]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_time = time.time()
        valid_entries = sum(
            1 for cached in self.cache.values()
            if current_time - cached.timestamp < self.cache_ttl
        )
        
        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_entries,
            'cache_hit_rate': valid_entries / max(len(self.cache), 1),
            'last_snapshot_age': current_time - self.last_snapshot_time
        }