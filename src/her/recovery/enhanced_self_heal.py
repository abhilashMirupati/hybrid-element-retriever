"""Enhanced self-healing locator recovery with DOM resnapshot and fallback strategies."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
import re
import time
from pathlib import Path

from ..bridge.cdp_bridge import capture_complete_snapshot, DOMSnapshot
from ..locator.synthesize import LocatorSynthesizer
from ..cache.two_tier import get_global_cache

logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import Page, Locator

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    Page = Any
    Locator = Any
    PLAYWRIGHT_AVAILABLE = False


class HealingStatus(Enum):
    """Status of healing attempt."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class HealingResult:
    """Result of a healing attempt."""

    status: HealingStatus
    original_locator: str
    healed_locators: List[str] = field(default_factory=list)
    selected_locator: Optional[str] = None
    confidence: float = 0.0
    strategy_used: Optional[str] = None
    attempts: int = 0
    duration_ms: int = 0
    error: Optional[str] = None
    dom_snapshot: Optional[DOMSnapshot] = None

    @property
    def success(self) -> bool:
        """Check if healing was successful."""
        return self.status == HealingStatus.SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "original_locator": self.original_locator,
            "healed_locators": self.healed_locators,
            "selected_locator": self.selected_locator,
            "confidence": self.confidence,
            "strategy_used": self.strategy_used,
            "attempts": self.attempts,
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


@dataclass
class HealingStrategy:
    """A self-healing strategy."""

    name: str
    description: str
    priority: int = 0
    max_attempts: int = 3
    requires_dom: bool = False

    def apply(
        self, locator: str, context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Apply healing strategy to generate alternative locators."""
        raise NotImplementedError


class RelaxExactMatchStrategy(HealingStrategy):
    """Relax exact match conditions to partial matches."""

    def __init__(self):
        super().__init__(
            name="relax_exact_match",
            description="Convert exact matches to contains() for flexibility",
            priority=1,
        )

    def apply(
        self, locator: str, context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Apply relaxation strategy."""
        alternatives = []

        # XPath text exact match to contains
        if "text()=" in locator:
            pattern = r"text\(\)\s*=\s*['\"]([^'\"]+)['\"]"
            relaxed = re.sub(pattern, r"contains(text(), '\1')", locator)
            alternatives.append(relaxed)

        # Attribute exact match to contains
        if "@" in locator and "=" in locator:
            pattern = r"@(\w+)\s*=\s*['\"]([^'\"]+)['\"]"
            relaxed = re.sub(pattern, r"contains(@\1, '\2')", locator)
            alternatives.append(relaxed)

        # Normalize space for text comparisons
        if "text()" in locator and "normalize-space" not in locator:
            normalized = locator.replace("text()", "normalize-space(text())")
            alternatives.append(normalized)

        return alternatives


class RemoveIndexStrategy(HealingStrategy):
    """Remove position indices from locators."""

    def __init__(self):
        super().__init__(
            name="remove_index",
            description="Remove array indices to find any matching element",
            priority=2,
        )

    def apply(
        self, locator: str, context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Remove indices from XPath."""
        alternatives = []

        # Remove [n] indices
        no_index = re.sub(r"\[\d+\]", "", locator)
        if no_index != locator:
            alternatives.append(no_index)

        # Replace [n] with [1] (first match)
        first_only = re.sub(r"\[\d+\]", "[1]", locator)
        if first_only != locator:
            alternatives.append(first_only)

        # Replace [n] with [last()] (last match)
        last_only = re.sub(r"\[\d+\]", "[last()]", locator)
        if last_only != locator:
            alternatives.append(last_only)

        return alternatives


class FuzzyTextStrategy(HealingStrategy):
    """Use fuzzy text matching."""

    def __init__(self):
        super().__init__(
            name="fuzzy_text",
            description="Use fuzzy text matching for resilience",
            priority=3,
        )

    def apply(
        self, locator: str, context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Apply fuzzy text matching."""
        alternatives = []

        # Extract text content
        text_match = re.search(r"text\(\)\s*=\s*['\"]([^'\"]+)['\"]", locator)
        if text_match:
            text = text_match.group(1)

            # Case insensitive
            case_insensitive = locator.replace(
                f"text()='{text}'",
                f"translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='{text.lower()}'",
            )
            alternatives.append(case_insensitive)

            # Starts with
            starts_with = locator.replace(
                f"text()='{text}'", f"starts-with(text(), '{text[:len(text)//2]}')"
            )
            alternatives.append(starts_with)

            # Contains key words
            words = text.split()
            if len(words) > 1:
                key_word = max(words, key=len)  # Longest word
                contains_key = locator.replace(
                    f"text()='{text}'", f"contains(text(), '{key_word}')"
                )
                alternatives.append(contains_key)

        return alternatives


class ParentChildStrategy(HealingStrategy):
    """Navigate to parent or child elements."""

    def __init__(self):
        super().__init__(
            name="parent_child",
            description="Try parent or child elements as alternatives",
            priority=4,
        )

    def apply(
        self, locator: str, context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Generate parent/child alternatives."""
        alternatives = []

        # Parent element
        if not locator.endswith("/.."):
            parent = f"{locator}/.."
            alternatives.append(parent)

        # Any child element
        any_child = f"{locator}//*"
        alternatives.append(any_child)

        # First child element
        first_child = f"{locator}/*[1]"
        alternatives.append(first_child)

        # Following sibling
        following = f"{locator}/following-sibling::*[1]"
        alternatives.append(following)

        # Preceding sibling
        preceding = f"{locator}/preceding-sibling::*[1]"
        alternatives.append(preceding)

        return alternatives


class DOMResnapshotStrategy(HealingStrategy):
    """Resnapshot DOM and regenerate locators."""

    def __init__(self, synthesizer: Optional[LocatorSynthesizer] = None):
        super().__init__(
            name="dom_resnapshot",
            description="Capture fresh DOM snapshot and regenerate locators",
            priority=5,
            requires_dom=True,
        )
        self.synthesizer = synthesizer or LocatorSynthesizer()

    def apply(
        self, locator: str, context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Resnapshot DOM and generate new locators."""
        if not context or "page" not in context:
            return []

        page = context["page"]
        alternatives = []

        try:
            # Capture fresh DOM snapshot
            snapshot = capture_complete_snapshot(page, wait_stable=True)

            # Extract element characteristics from original locator
            element_hints = self._extract_element_hints(locator)

            # Find similar elements in new snapshot
            candidates = self._find_similar_elements(snapshot, element_hints)

            # Generate locators for candidates
            for candidate in candidates[:5]:  # Top 5 candidates
                new_locators = self.synthesizer.synthesize(candidate)
                alternatives.extend(new_locators)

            # Store snapshot for analysis
            if context:
                context["dom_snapshot"] = snapshot

        except Exception as e:
            logger.error(f"DOM resnapshot failed: {e}")

        return alternatives

    def _extract_element_hints(self, locator: str) -> Dict[str, Any]:
        """Extract element characteristics from locator."""
        hints = {}

        # Extract tag name
        tag_match = re.search(r"//(\w+)", locator)
        if tag_match:
            hints["tag"] = tag_match.group(1)

        # Extract ID
        id_match = re.search(r"@id\s*=\s*['\"]([^'\"]+)['\"]", locator)
        if id_match:
            hints["id"] = id_match.group(1)

        # Extract class
        class_match = re.search(r"@class\s*=\s*['\"]([^'\"]+)['\"]", locator)
        if class_match:
            hints["class"] = class_match.group(1)

        # Extract text
        text_match = re.search(r"text\(\)\s*=\s*['\"]([^'\"]+)['\"]", locator)
        if not text_match:
            text_match = re.search(
                r"contains\(text\(\),\s*['\"]([^'\"]+)['\"]", locator
            )
        if text_match:
            hints["text"] = text_match.group(1)

        return hints

    def _find_similar_elements(
        self, snapshot: DOMSnapshot, hints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find elements similar to hints in snapshot."""
        candidates = []

        for node in snapshot.dom_nodes:
            score = 0.0

            # Check tag match
            if "tag" in hints and node.get("localName") == hints["tag"]:
                score += 0.3

            # Check ID similarity
            attributes = {a["name"]: a["value"] for a in node.get("attributes", [])}
            if "id" in hints and "id" in attributes:
                if attributes["id"] == hints["id"]:
                    score += 0.4
                elif hints["id"] in attributes["id"] or attributes["id"] in hints["id"]:
                    score += 0.2

            # Check class similarity
            if "class" in hints and "class" in attributes:
                hint_classes = set(hints["class"].split())
                node_classes = set(attributes["class"].split())
                if hint_classes & node_classes:  # Intersection
                    score += 0.2

            # Check text similarity
            if "text" in hints and node.get("nodeValue"):
                if hints["text"] in str(node["nodeValue"]):
                    score += 0.1

            if score > 0.3:  # Threshold for similarity
                candidates.append(
                    {"node": node, "score": score, "attributes": attributes}
                )

        # Sort by score
        candidates.sort(key=lambda x: x["score"], reverse=True)

        return candidates


class EnhancedSelfHeal:
    """Enhanced self-healing system with multiple strategies and DOM resnapshot."""

    def __init__(self, cache_healed: bool = True):
        """Initialize enhanced self-healer.

        Args:
            cache_healed: Whether to cache successful healings
        """
        self.strategies = self._init_strategies()
        self.healing_history: List[HealingResult] = []
        self.cache_healed = cache_healed
        self.cache = get_global_cache() if cache_healed else None

    def _init_strategies(self) -> List[HealingStrategy]:
        """Initialize healing strategies in priority order."""
        return [
            RelaxExactMatchStrategy(),
            RemoveIndexStrategy(),
            FuzzyTextStrategy(),
            ParentChildStrategy(),
            DOMResnapshotStrategy(),
        ]

    def heal(
        self,
        failed_locator: str,
        page: Optional[Page] = None,
        context: Optional[Dict[str, Any]] = None,
        max_attempts: int = 3,
        resnapshot_on_fail: bool = True,
    ) -> HealingResult:
        """Attempt to heal a failed locator.

        Args:
            failed_locator: The locator that failed
            page: Page instance for testing healed locators
            context: Context about the failure
            max_attempts: Maximum healing attempts
            resnapshot_on_fail: Whether to resnapshot DOM on failure

        Returns:
            Healing result
        """
        start_time = time.time()

        result = HealingResult(
            status=HealingStatus.FAILED, original_locator=failed_locator, attempts=0
        )

        # Check cache first
        if self.cache:
            cache_key = self.cache.compute_key("healed", failed_locator)
            cached_healed = self.cache.get(cache_key)
            if cached_healed:
                result.status = HealingStatus.SUCCESS
                result.selected_locator = cached_healed
                result.healed_locators = [cached_healed]
                result.confidence = 1.0
                result.strategy_used = "cached"
                logger.info(f"Using cached healed locator: {cached_healed}")
                return result

        # Prepare context
        if context is None:
            context = {}
        if page:
            context["page"] = page

        # Try each strategy
        for strategy in sorted(self.strategies, key=lambda s: s.priority):
            if result.attempts >= max_attempts:
                break

            logger.debug(f"Trying healing strategy: {strategy.name}")

            # Skip DOM-requiring strategies if no page
            if strategy.requires_dom and not page:
                continue

            try:
                # Generate alternative locators
                alternatives = strategy.apply(failed_locator, context)

                for alt_locator in alternatives:
                    if alt_locator and alt_locator != failed_locator:
                        result.healed_locators.append(alt_locator)
                        result.attempts += 1

                        # Test if page provided
                        if page:
                            if self._test_locator(page, alt_locator):
                                result.status = HealingStatus.SUCCESS
                                result.selected_locator = alt_locator
                                result.confidence = 0.8  # Base confidence
                                result.strategy_used = strategy.name

                                # Cache successful healing
                                if self.cache:
                                    self.cache.put(cache_key, alt_locator)

                                logger.info(
                                    f"Healed locator using {strategy.name}: {alt_locator}"
                                )
                                break
                        else:
                            # No page to test, assume first alternative
                            result.status = HealingStatus.PARTIAL
                            result.selected_locator = alt_locator
                            result.confidence = 0.5
                            result.strategy_used = strategy.name
                            break

                if result.status in [HealingStatus.SUCCESS, HealingStatus.PARTIAL]:
                    break

            except Exception as e:
                logger.error(f"Strategy {strategy.name} failed: {e}")
                result.error = str(e)

        # Last resort: DOM resnapshot
        if result.status == HealingStatus.FAILED and resnapshot_on_fail and page:
            logger.info("Attempting DOM resnapshot as last resort")
            resnapshot_strategy = DOMResnapshotStrategy()

            try:
                alternatives = resnapshot_strategy.apply(failed_locator, context)
                for alt_locator in alternatives[:3]:  # Try top 3
                    if self._test_locator(page, alt_locator):
                        result.status = HealingStatus.SUCCESS
                        result.selected_locator = alt_locator
                        result.confidence = 0.6
                        result.strategy_used = "dom_resnapshot"
                        result.dom_snapshot = context.get("dom_snapshot")
                        break
            except Exception as e:
                logger.error(f"DOM resnapshot failed: {e}")

        # Calculate duration
        result.duration_ms = int((time.time() - start_time) * 1000)

        # Store in history
        self.healing_history.append(result)

        # Log result
        if result.success:
            logger.info(
                f"Successfully healed locator in {result.duration_ms}ms "
                f"using {result.strategy_used}: {result.selected_locator}"
            )
        else:
            logger.warning(
                f"Failed to heal locator after {result.attempts} attempts "
                f"in {result.duration_ms}ms"
            )

        return result

    def _test_locator(self, page: Page, locator: str) -> bool:
        """Test if a locator finds an element.

        Args:
            page: Page instance
            locator: Locator to test

        Returns:
            True if locator finds at least one element
        """
        if not page or not PLAYWRIGHT_AVAILABLE:
            return False

        try:
            # Try to find element
            element = page.locator(locator)

            # Check if exists and visible
            if element.count() > 0:
                # Try to check visibility of first match
                try:
                    is_visible = element.first.is_visible(timeout=1000)
                    return is_visible
                except Exception:
                    # Element exists but may not be visible
                    return True

            return False

        except Exception as e:
            logger.debug(f"Locator test failed for {locator}: {e}")
            return False

    def heal_and_execute(
        self,
        page: Page,
        primary_locator: str,
        action: str = "click",
        args: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute action with self-healing fallback.
        
        Args:
            page: Playwright page instance
            primary_locator: Primary locator that failed
            action: Action to perform
            args: Arguments for the action
            
        Returns:
            Dictionary with execution results
        """
        # This is the main healing method - delegates to internal implementation
        # The actual implementation is complex and spread across multiple methods
        
        result = {
            "success": False,
            "used_locator": primary_locator,
            "attempts": 1,
            "healed": False
        }
        
        # Try primary locator first
        if self._test_locator(page, primary_locator):
            try:
                element = page.query_selector(primary_locator)
                if element:
                    if action == "click":
                        element.click()
                    elif action == "fill" and args:
                        element.fill(args)
                    elif action == "check":
                        element.check()
                    result["success"] = True
                    return result
            except Exception:
                pass
        
        # Get fallback locators
        fallbacks = self.get_fallback_locators(primary_locator)
        
        # Try each fallback
        for fallback in fallbacks:
            if self._test_locator(page, fallback):
                try:
                    element = page.query_selector(fallback)
                    if element:
                        if action == "click":
                            element.click()
                        elif action == "fill" and args:
                            element.fill(args)
                        elif action == "check":
                            element.check()
                        
                        result["success"] = True
                        result["used_locator"] = fallback
                        result["healed"] = True
                        result["attempts"] += 1
                        
                        # Cache successful healing
                        if self.cache_healed:
                            self.healed_cache[primary_locator] = fallback
                        
                        return result
                except Exception:
                    result["attempts"] += 1
                    continue
        
        return result
    
    def generate_fallbacks(self, primary_locator: str, count: int = 5) -> List[str]:
        """Generate fallback locators for a primary locator.
        
        Args:
            primary_locator: The primary locator
            count: Number of fallbacks to generate
            
        Returns:
            List of fallback locators
        """
        # Alias for get_fallback_locators for compatibility
        return self.get_fallback_locators(primary_locator, count)
    
    def get_fallback_locators(self, primary_locator: str, count: int = 3) -> List[str]:
        """Generate fallback locators proactively.

        Args:
            primary_locator: Primary locator
            count: Number of fallbacks to generate

        Returns:
            List of fallback locators
        """
        fallbacks = []

        # Apply each strategy to generate alternatives
        for strategy in self.strategies[:count]:
            try:
                alternatives = strategy.apply(primary_locator)
                fallbacks.extend(alternatives)
            except Exception:
                # Alternative generation failed, continue with other methods
                continue

        # Remove duplicates while preserving order
        seen = set()
        unique_fallbacks = []
        for fb in fallbacks:
            if fb not in seen and fb != primary_locator:
                seen.add(fb)
                unique_fallbacks.append(fb)

        return unique_fallbacks[:count]

    
    def get_stats(self) -> Dict[str, Any]:
        """Get healing statistics."""
        if not self.healing_history:
            return {"total_healings": 0, "success_rate": 0.0}

        successful = sum(1 for r in self.healing_history if r.success)
        total = len(self.healing_history)

        strategy_usage = {}
        for result in self.healing_history:
            if result.strategy_used:
                strategy_usage[result.strategy_used] = (
                    strategy_usage.get(result.strategy_used, 0) + 1
                )

        return {
            "total_healings": total,
            "successful": successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "avg_attempts": sum(r.attempts for r in self.healing_history) / total,
            "avg_duration_ms": sum(r.duration_ms for r in self.healing_history) / total,
            "strategy_usage": strategy_usage,
            "cached_healings": sum(
                1 for r in self.healing_history if r.strategy_used == "cached"
            ),
        }


# Alias for compatibility
EnhancedSelfHealer = EnhancedSelfHeal
