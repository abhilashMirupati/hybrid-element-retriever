"""Self-healing functionality for HER."""

from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass

from .promotion import PromotionStore


@dataclass
class HealResult:
    """Result of a self-heal attempt."""
    ok: bool
    strategy: Optional[str] = None
    selector: Optional[str] = None
    confidence_boost: float = 0.0
    reason: str = ""


class SelfHealer:
    """Self-healing system that learns from successful interactions."""
    
    def __init__(self, store: PromotionStore, verify_fn: Callable, 
                 require_unique: bool = True, min_confidence: float = 0.8):
        """Initialize the self-healer.
        
        Args:
            store: Promotion store for caching
            verify_fn: Function to verify selectors
            require_unique: Whether to require unique selectors
            min_confidence: Minimum confidence threshold
        """
        self.store = store
        self.verify_fn = verify_fn
        self.require_unique = require_unique
        self.min_confidence = min_confidence
    
    def try_cached(self, page: Any, query: str, context_url: str = "", 
                   dom_hash: str = "", extra_context: Optional[Dict[str, Any]] = None) -> HealResult:
        """Try to find a cached solution for the query.
        
        Args:
            page: Page object (may be None for offline mode)
            query: The query to solve
            context_url: Current page URL
            dom_hash: Hash of current DOM
            extra_context: Additional context
            
        Returns:
            HealResult with success status and selector if found
        """
        # Look up cached solutions
        cached = self.store.lookup(query, context_url, dom_hash)
        
        if not cached:
            return HealResult(ok=False, reason="no_cached_solutions")
        
        # Try each cached solution
        for solution in cached:
            strategy = solution["strategy"]
            selector = solution["selector"]
            confidence = solution["confidence"]
            
            if confidence < self.min_confidence:
                continue
            
            # Verify the selector (if page is available)
            if page is not None:
                try:
                    verify_result = self.verify_fn(
                        page, selector, 
                        strategy=strategy, 
                        require_unique=self.require_unique
                    )
                    if verify_result.ok:
                        return HealResult(
                            ok=True,
                            strategy=strategy,
                            selector=selector,
                            confidence_boost=confidence * 0.1,  # Small boost
                            reason="cached_verified"
                        )
                except Exception:
                    continue
            else:
                # Offline mode - trust cached solutions
                return HealResult(
                    ok=True,
                    strategy=strategy,
                    selector=selector,
                    confidence_boost=confidence * 0.1,
                    reason="cached_offline"
                )
        
        return HealResult(ok=False, reason="cached_solutions_failed_verification")
    
    def learn_success(self, query: str, strategy: str, selector: str, 
                     confidence: float = 1.0, url: str = "", 
                     dom_hash: str = "", context: Optional[Dict[str, Any]] = None) -> None:
        """Learn from a successful interaction.
        
        Args:
            query: The query that succeeded
            strategy: The strategy used
            selector: The successful selector
            confidence: Confidence in the success
            url: URL where this worked
            dom_hash: DOM hash when this worked
            context: Additional context
        """
        self.store.store(
            query=query,
            strategy=strategy,
            selector=selector,
            confidence=confidence,
            url=url,
            dom_hash=dom_hash,
            context=context
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the self-healer."""
        # This would need to be implemented based on the store backend
        return {
            "cached_solutions": 0,  # Would need to query store
            "success_rate": 0.0,    # Would need to track successes/failures
            "avg_confidence": 0.0   # Would need to calculate from store
        }