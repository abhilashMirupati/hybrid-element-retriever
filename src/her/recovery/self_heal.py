"""Self-healing locator recovery with multiple strategies."""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging
import re

logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    Page = Any
    PLAYWRIGHT_AVAILABLE = False


@dataclass
class HealingStrategy:
    """A self-healing strategy."""
    name: str
    description: str
    transform_func: Any  # Callable[[str], str]
    priority: int = 0


class SelfHealer:
    """Self-healing locator recovery system."""
    
    def __init__(self):
        self.strategies = self._init_strategies()
        self.healing_history: List[Dict[str, Any]] = []
    
    def _init_strategies(self) -> List[HealingStrategy]:
        """Initialize healing strategies."""
        return [
            HealingStrategy(
                name="relax_exact_match",
                description="Relax exact match to contains",
                transform_func=self._relax_exact_match,
                priority=1
            ),
            HealingStrategy(
                name="remove_index",
                description="Remove position index from XPath",
                transform_func=self._remove_index,
                priority=2
            ),
            HealingStrategy(
                name="id_to_contains",
                description="Change ID exact match to contains",
                transform_func=self._id_to_contains,
                priority=3
            ),
            HealingStrategy(
                name="class_to_contains",
                description="Change class exact match to contains",
                transform_func=self._class_to_contains,
                priority=4
            ),
            HealingStrategy(
                name="text_to_partial",
                description="Use partial text match",
                transform_func=self._text_to_partial,
                priority=5
            ),
            HealingStrategy(
                name="remove_attributes",
                description="Remove specific attributes from selector",
                transform_func=self._remove_attributes,
                priority=6
            ),
            HealingStrategy(
                name="tag_only",
                description="Use only tag name",
                transform_func=self._tag_only,
                priority=7
            ),
            HealingStrategy(
                name="parent_child",
                description="Try parent or child element",
                transform_func=self._parent_child,
                priority=8
            ),
        ]
    
    def heal(
        self,
        failed_locator: str,
        page: Optional[Page] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, str]]:
        """Attempt to heal a failed locator.
        
        Args:
            failed_locator: The locator that failed
            page: Optional page for testing healed locators
            context: Optional context about the failure
        
        Returns:
            List of (healed_locator, strategy_name) tuples
        """
        healed_locators = []
        
        # Sort strategies by priority
        sorted_strategies = sorted(self.strategies, key=lambda s: s.priority)
        
        for strategy in sorted_strategies:
            try:
                healed = strategy.transform_func(failed_locator)
                if healed and healed != failed_locator:
                    # Test if healed locator works
                    if page and PLAYWRIGHT_AVAILABLE:
                        try:
                            element = page.locator(healed)
                            if element.count() > 0:
                                healed_locators.append((healed, strategy.name))
                                logger.info(f"Healed locator using {strategy.name}: {healed}")
                        except Exception as test_error:
                            logger.debug(f"Failed to test healed locator: {test_error}")
                    else:
                        # No page to test, just add the healed version
                        healed_locators.append((healed, strategy.name))
            except Exception as e:
                logger.debug(f"Strategy {strategy.name} failed: {e}")
        
        # Record healing attempt
        self.healing_history.append({
            "failed_locator": failed_locator,
            "healed_count": len(healed_locators),
            "strategies_used": [s for _, s in healed_locators],
            "context": context
        })
        
        return healed_locators
    
    def _relax_exact_match(self, locator: str) -> str:
        """Relax exact match to contains."""
        # XPath exact match to contains
        if "text()=" in locator:
            return locator.replace("text()=", "contains(text(),")
        
        # CSS/XPath attribute exact match to contains
        if "[@" in locator and "='" in locator:
            # Change [@id='value'] to [contains(@id, 'value')]
            pattern = r"\[@(\w+)='([^']+)'\]"
            return re.sub(pattern, r"[contains(@\1, '\2')]", locator)
        
        # CSS attribute selector
        if "[" in locator and "=\"" in locator:
            # Change [attr="value"] to [attr*="value"]
            return re.sub(r'\[(\w+)="([^"]+)"\]', r'[\1*="\2"]', locator)
        
        return locator
    
    def _remove_index(self, locator: str) -> str:
        """Remove position index from XPath."""
        # Remove [1], [2], etc. from XPath
        return re.sub(r'\[\d+\]', '', locator)
    
    def _id_to_contains(self, locator: str) -> str:
        """Change ID exact match to contains."""
        # XPath
        if "@id='" in locator:
            return locator.replace("@id='", "contains(@id, '")
        
        # CSS
        if "#" in locator:
            # Extract ID and convert to attribute selector
            match = re.search(r'#([\w-]+)', locator)
            if match:
                id_value = match.group(1)
                return locator.replace(f"#{id_value}", f"[id*='{id_value}']")
        
        return locator
    
    def _class_to_contains(self, locator: str) -> str:
        """Change class exact match to contains."""
        # XPath
        if "@class='" in locator:
            return locator.replace("@class='", "contains(@class, '")
        
        # CSS class selector
        if "." in locator:
            # Convert .class1.class2 to [class*="class1"][class*="class2"]
            classes = re.findall(r'\.([^\s.#\[]+)', locator)
            if classes:
                tag_match = re.match(r'^(\w+)', locator)
                tag = tag_match.group(1) if tag_match else ""
                class_selectors = "".join(f"[class*='{cls}']" for cls in classes)
                return f"{tag}{class_selectors}"
        
        return locator
    
    def _text_to_partial(self, locator: str) -> str:
        """Use partial text match."""
        # Extract text content and use first/last words
        text_match = re.search(r"text\(\)='([^']+)'", locator)
        if text_match:
            text = text_match.group(1)
            words = text.split()
            if len(words) > 2:
                # Use first and last word
                partial = f"{words[0]}.*{words[-1]}"
                return locator.replace(f"text()='{text}'", f"contains(text(), '{words[0]}')")
        
        # CSS text selector
        if "text=" in locator:
            text_match = re.search(r'text="([^"]+)"', locator)
            if text_match:
                text = text_match.group(1)
                words = text.split()
                if words:
                    return f"text*=\"{words[0]}\""
        
        return locator
    
    def _remove_attributes(self, locator: str) -> str:
        """Remove specific attributes from selector."""
        # Remove data- attributes
        locator = re.sub(r'\[data-[^=]+=["\'"][^"\']*["\']\]', '', locator)
        
        # Remove aria- attributes
        locator = re.sub(r'\[aria-[^=]+=["\'"][^"\']*["\']\]', '', locator)
        
        # Remove style attribute
        locator = re.sub(r'\[style[^]]*\]', '', locator)
        
        return locator
    
    def _tag_only(self, locator: str) -> str:
        """Use only tag name."""
        # Extract tag from XPath
        if locator.startswith("//"):
            tag_match = re.match(r'//(\w+)', locator)
            if tag_match:
                return f"//{tag_match.group(1)}"
        
        # Extract tag from CSS
        tag_match = re.match(r'^(\w+)', locator)
        if tag_match:
            return tag_match.group(1)
        
        return locator
    
    def _parent_child(self, locator: str) -> str:
        """Try parent or child element."""
        # Add parent axis to XPath
        if locator.startswith("//"):
            return f"{locator}/parent::*"
        
        # Add parent selector to CSS
        if not locator.startswith("//"):
            return f"{locator} > *"
        
        return locator
    
    def add_strategy(self, strategy: HealingStrategy) -> None:
        """Add a custom healing strategy."""
        self.strategies.append(strategy)
        logger.info(f"Added healing strategy: {strategy.name}")
    
    def get_healing_stats(self) -> Dict[str, Any]:
        """Get statistics about healing attempts."""
        if not self.healing_history:
            return {
                "total_attempts": 0,
                "successful_heals": 0,
                "success_rate": 0.0,
                "most_used_strategies": []
            }
        
        total = len(self.healing_history)
        successful = sum(1 for h in self.healing_history if h["healed_count"] > 0)
        
        # Count strategy usage
        strategy_counts = {}
        for history in self.healing_history:
            for strategy in history["strategies_used"]:
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        most_used = sorted(strategy_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_attempts": total,
            "successful_heals": successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "most_used_strategies": most_used
        }