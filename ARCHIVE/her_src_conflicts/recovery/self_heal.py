# archived duplicate of src/her/recovery/self_heal.py
"""Self-healing locator recovery."""

import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json

from her.bridge.snapshot import DOMNode
from her.locator.synthesize import LocatorSynthesizer, SynthesizedLocator
from her.locator.verify import LocatorVerifier, VerificationResult

logger = logging.getLogger(__name__)


@dataclass
class HealingResult:
    """Result of self-healing attempt."""
    success: bool
    original_selector: str
    healed_selector: Optional[str]
    strategy: str
    attempts: int
    healing_method: Optional[str]
    confidence: float
    

class SelfHealer:
    """Self-healing locator recovery system."""
    
    def __init__(self, verifier: LocatorVerifier):
        self.verifier = verifier
        self.synthesizer = LocatorSynthesizer()
        self._healing_history: Dict[str, str] = {}  # Maps failed -> successful
        
    async def heal(
        self,
        failed_selector: str,
        strategy: str,
        candidate_nodes: List[DOMNode],
        frame_path: Optional[List[str]] = None
    ) -> HealingResult:
        """Attempt to heal a failed selector.
        
        Args:
            failed_selector: Selector that failed
            strategy: Original strategy
            candidate_nodes: Candidate nodes to try
            frame_path: Frame path if in iframe
            
        Returns:
            HealingResult with healed selector if successful
        """
        logger.info(f"Attempting to heal selector: {failed_selector}")
        
        # Check history first
        if failed_selector in self._healing_history:
            historical = self._healing_history[failed_selector]
            verification = await self.verifier.verify(
                selector=historical,
                strategy=strategy,
                frame_path=frame_path
            )
            if verification.ok:
                logger.info(f"Healed from history: {historical}")
                return HealingResult(
                    success=True,
                    original_selector=failed_selector,
                    healed_selector=historical,
                    strategy=strategy,
                    attempts=1,
                    healing_method='history',
                    confidence=0.9
                )
                
        # Try different healing methods
        attempts = 0
        
        # Method 1: Try alternative selectors for top candidates
        for node in candidate_nodes[:5]:  # Top 5 candidates
            attempts += 1
            
            # Synthesize new locator
            synthesized = self.synthesizer.synthesize(node, candidate_nodes)
            
            # Verify it works
            verification = await self.verifier.verify(
                selector=synthesized.selector,
                strategy=synthesized.strategy,
                frame_path=frame_path,
                alternatives=synthesized.alternatives
            )
            
            if verification.ok:
                # Found working selector
                healed_selector = verification.used_selector
                
                # Store in history
                self._healing_history[failed_selector] = healed_selector
                
                logger.info(f"Healed selector: {healed_selector} (method: synthesis)")
                
                return HealingResult(
                    success=True,
                    original_selector=failed_selector,
                    healed_selector=healed_selector,
                    strategy=verification.strategy,
                    attempts=attempts,
                    healing_method='synthesis',
                    confidence=synthesized.confidence
                )
                
        # Method 2: Try relaxing the selector
        relaxed = self._relax_selector(failed_selector, strategy)
        if relaxed and relaxed != failed_selector:
            attempts += 1
            verification = await self.verifier.verify(
                selector=relaxed,
                strategy=strategy,
                frame_path=frame_path
            )
            
            if verification.ok:
                self._healing_history[failed_selector] = relaxed
                
                logger.info(f"Healed by relaxing: {relaxed}")
                
                return HealingResult(
                    success=True,
                    original_selector=failed_selector,
                    healed_selector=relaxed,
                    strategy=strategy,
                    attempts=attempts,
                    healing_method='relaxation',
                    confidence=0.6
                )
                
        # Method 3: Try partial matching
        partial = self._create_partial_selector(failed_selector, strategy)
        if partial and partial != failed_selector:
            attempts += 1
            verification = await self.verifier.verify(
                selector=partial,
                strategy=strategy,
                frame_path=frame_path
            )
            
            if verification.ok and verification.unique:
                self._healing_history[failed_selector] = partial
                
                logger.info(f"Healed by partial match: {partial}")
                
                return HealingResult(
                    success=True,
                    original_selector=failed_selector,
                    healed_selector=partial,
                    strategy=strategy,
                    attempts=attempts,
                    healing_method='partial',
                    confidence=0.5
                )
                
        # Healing failed
        logger.warning(f"Failed to heal selector after {attempts} attempts")
        
        return HealingResult(
            success=False,
            original_selector=failed_selector,
            healed_selector=None,
            strategy=strategy,
            attempts=attempts,
            healing_method=None,
            confidence=0.0
        )
        
    def _relax_selector(self, selector: str, strategy: str) -> Optional[str]:
        """Relax a selector to be less specific.
        
        Args:
            selector: Original selector
            strategy: Selector strategy
            
        Returns:
            Relaxed selector or None
        """
        if strategy == 'css':
            # Remove pseudo-selectors
            relaxed = selector
            for pseudo in [':first', ':last', ':nth-child', ':nth-of-type']:
                if pseudo in relaxed:
                    idx = relaxed.find(pseudo)
                    # Find end of pseudo-selector
                    end = relaxed.find(')', idx) + 1 if '(' in relaxed[idx:] else idx + len(pseudo)
                    relaxed = relaxed[:idx] + relaxed[end:]
                    
            # Remove attribute selectors
            import re
            relaxed = re.sub(r'\[[^\]]+\]', '', relaxed)
            
            # Remove classes one by one
            if '.' in relaxed:
                parts = relaxed.split('.')
                if len(parts) > 2:  # Has multiple classes
                    relaxed = parts[0] + '.' + parts[1]  # Keep first class only
                    
            return relaxed if relaxed != selector else None
            
        elif strategy == 'xpath':
            # Remove position predicates
            import re
            relaxed = re.sub(r'\[\d+\]', '', selector)
            
            # Remove complex conditions
            if ' and ' in selector:
                # Keep only first condition
                start = selector.find('[')
                end = selector.find(']')
                if start > 0 and end > start:
                    conditions = selector[start+1:end].split(' and ')
                    if conditions:
                        relaxed = selector[:start+1] + conditions[0] + selector[end:]
                        
            return relaxed if relaxed != selector else None
            
        return None
        
    def _create_partial_selector(self, selector: str, strategy: str) -> Optional[str]:
        """Create a partial match selector.
        
        Args:
            selector: Original selector
            strategy: Selector strategy
            
        Returns:
            Partial selector or None
        """
        if strategy == 'css':
            # Extract most specific part
            if '#' in selector:
                # Keep ID only
                import re
                id_match = re.search(r'#([\w-]+)', selector)
                if id_match:
                    return f"#{id_match.group(1)}"
                    
            # Keep tag and first class
            import re
            tag_match = re.match(r'^(\w+)', selector)
            class_match = re.search(r'\.([\w-]+)', selector)
            
            if tag_match and class_match:
                return f"{tag_match.group(1)}.{class_match.group(1)}"
            elif tag_match:
                return tag_match.group(1)
                
        elif strategy == 'xpath':
            # Simplify to tag name with single condition
            import re
            
            # Extract tag
            tag_match = re.search(r'//?(\w+)', selector)
            if not tag_match:
                return None
                
            tag = tag_match.group(1)
            
            # Extract most important condition
            if '@id=' in selector:
                id_match = re.search(r"@id='([^']+)'", selector)
                if id_match:
                    return f"//{tag}[@id='{id_match.group(1)}']"
                    
            if 'text()' in selector:
                text_match = re.search(r"text\(\)[^']*'([^']+)'", selector)
                if text_match:
                    return f"//{tag}[contains(text(), '{text_match.group(1)}')]"
                    
            # Just tag name
            return f"//{tag}"
            
        return None
        
    def get_healing_stats(self) -> Dict[str, any]:
        """Get healing statistics.
        
        Returns:
            Dictionary of stats
        """
        return {
            'total_healed': len(self._healing_history),
            'unique_failures': len(set(self._healing_history.keys())),
            'history_size': len(self._healing_history)
        }
        
    def export_healing_history(self) -> str:
        """Export healing history as JSON.
        
        Returns:
            JSON string of healing history
        """
        return json.dumps(self._healing_history, indent=2)
        
    def import_healing_history(self, history_json: str) -> None:
        """Import healing history from JSON.
        
        Args:
            history_json: JSON string of healing history
        """
        try:
            imported = json.loads(history_json)
            self._healing_history.update(imported)
            logger.info(f"Imported {len(imported)} healing mappings")
        except Exception as e:
            logger.error(f"Failed to import healing history: {e}")