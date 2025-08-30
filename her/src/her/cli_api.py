"""Main API for HER framework."""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path

from playwright.async_api import async_playwright, Browser, Page
import numpy as np

from her.bridge.snapshot import Snapshot
from her.executor.session import Session
from her.executor.actions import ActionExecutor, ActionType
from her.embeddings.query_embedder import QueryEmbedder
from her.embeddings.element_embedder import ElementEmbedder
from her.vectordb.sqlite_cache import VectorCache
from her.rank.fusion import FusionRanker
from her.locator.synthesize import LocatorSynthesizer
from her.locator.verify import LocatorVerifier
from her.recovery.self_heal import SelfHealer
from her.recovery.promotion import PromotionManager

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Result of element query."""
    success: bool
    selector: str
    strategy: str
    confidence: float
    frame_path: List[str]
    alternatives: List[str]
    verification: Dict[str, Any]
    timing: Dict[str, float]
    metadata: Dict[str, Any]
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(asdict(self), indent=2)
        

@dataclass
class ActionResult:
    """Result of action execution."""
    success: bool
    action: str
    selector: str
    value: Optional[Any]
    waits: Dict[str, float]
    frame: Dict[str, Any]
    post_action: Dict[str, Any]
    timing: Dict[str, float]
    error: Optional[str]
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(asdict(self), indent=2)
        

class HybridClient:
    """Main client for HER framework.
    
    Provides high-level API for querying and acting on web elements.
    """
    
    def __init__(
        self,
        headless: bool = True,
        cache_dir: Optional[Path] = None,
        auto_heal: bool = True,
        use_promotion: bool = True
    ):
        self.headless = headless
        self.cache_dir = cache_dir or Path(".cache")
        self.auto_heal = auto_heal
        self.use_promotion = use_promotion
        
        # Components (initialized on start)
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.session: Optional[Session] = None
        self.query_embedder: Optional[QueryEmbedder] = None
        self.element_embedder: Optional[ElementEmbedder] = None
        self.vector_cache: Optional[VectorCache] = None
        self.ranker: Optional[FusionRanker] = None
        self.synthesizer: Optional[LocatorSynthesizer] = None
        self.verifier: Optional[LocatorVerifier] = None
        self.executor: Optional[ActionExecutor] = None
        self.healer: Optional[SelfHealer] = None
        self.promotion: Optional[PromotionManager] = None
        
        self._playwright = None
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize all components."""
        if self._initialized:
            return
            
        logger.info("Initializing HER client...")
        
        # Start Playwright
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        
        # Initialize components
        self.session = Session(self.page)
        await self.session.initialize()
        
        self.query_embedder = QueryEmbedder()
        self.element_embedder = ElementEmbedder()
        
        self.vector_cache = VectorCache(self.cache_dir / "embeddings")
        await self.vector_cache.initialize()
        
        self.ranker = FusionRanker()
        self.synthesizer = LocatorSynthesizer()
        self.verifier = LocatorVerifier(self.page)
        self.executor = ActionExecutor(self.page)
        
        if self.auto_heal:
            self.healer = SelfHealer(self.verifier)
            
        if self.use_promotion:
            self.promotion = PromotionManager(self.cache_dir)
            await self.promotion.initialize()
            
        self._initialized = True
        logger.info("HER client initialized")
        
    async def close(self) -> None:
        """Close all resources."""
        if self.vector_cache:
            await self.vector_cache.close()
        if self.promotion:
            await self.promotion.close()
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
            
        self._initialized = False
        logger.info("HER client closed")
        
    async def query(
        self,
        phrase: str,
        url: Optional[str] = None,
        wait_stable: bool = True
    ) -> QueryResult:
        """Query for an element using natural language.
        
        Args:
            phrase: Natural language query
            url: Optional URL to navigate to
            wait_stable: Wait for DOM to stabilize
            
        Returns:
            QueryResult with located element
        """
        if not self._initialized:
            await self.initialize()
            
        start_time = time.time()
        timing = {}
        
        # Navigate if URL provided
        if url:
            await self.page.goto(url)
            timing['navigation'] = time.time() - start_time
            
        # Wait for stable DOM
        if wait_stable:
            await self.session.wait_for_stable_dom()
            timing['stabilization'] = time.time() - start_time - timing.get('navigation', 0)
            
        # Take snapshot
        snapshot_start = time.time()
        snapshot = await self.session.take_snapshot()
        timing['snapshot'] = time.time() - snapshot_start
        
        # Embed query
        embed_start = time.time()
        query_embedding = self.query_embedder.embed(phrase)
        timing['query_embedding'] = time.time() - embed_start
        
        # Process main frame (simplified - would handle all frames in production)
        main_frame = snapshot.frames[0] if snapshot.frames else None
        if not main_frame:
            return QueryResult(
                success=False,
                selector="",
                strategy="",
                confidence=0.0,
                frame_path=[],
                alternatives=[],
                verification={"error": "No frames found"},
                timing=timing,
                metadata={"error": "No frames in snapshot"}
            )
            
        # Filter clickable/interactive elements
        interactive_nodes = [
            node for node in main_frame.dom_nodes
            if node.is_visible and (
                node.is_clickable or
                node.node_name.lower() in ['input', 'select', 'textarea', 'button', 'a']
            )
        ]
        
        # Embed elements
        element_start = time.time()
        element_embeddings = self.element_embedder.batch_embed(interactive_nodes)
        timing['element_embedding'] = time.time() - element_start
        
        # Get promotion scores if enabled
        promotion_scores = {}
        if self.use_promotion:
            backend_ids = [n.backend_node_id for n in interactive_nodes]
            promotion_scores = await self.promotion.get_promotion_scores(
                self.page.url,
                backend_ids
            )
            
        # Rank elements
        rank_start = time.time()
        ranking_results = self.ranker.rank(
            query_embedding,
            element_embeddings,
            interactive_nodes,
            phrase,
            promotion_scores
        )
        timing['ranking'] = time.time() - rank_start
        
        if not ranking_results:
            return QueryResult(
                success=False,
                selector="",
                strategy="",
                confidence=0.0,
                frame_path=[],
                alternatives=[],
                verification={"error": "No elements ranked"},
                timing=timing,
                metadata={"error": "No matching elements"}
            )
            
        # Get top result
        top_result = ranking_results[0]
        
        # Synthesize locator
        synth_start = time.time()
        synthesized = self.synthesizer.synthesize(
            top_result.node,
            interactive_nodes
        )
        timing['synthesis'] = time.time() - synth_start
        
        # Verify locator
        verify_start = time.time()
        verification = await self.verifier.verify(
            synthesized.selector,
            synthesized.strategy,
            alternatives=synthesized.alternatives
        )
        timing['verification'] = time.time() - verify_start
        
        # Try self-healing if verification failed
        if not verification.ok and self.auto_heal:
            heal_start = time.time()
            healing_result = await self.healer.heal(
                synthesized.selector,
                synthesized.strategy,
                [r.node for r in ranking_results[:5]]
            )
            
            if healing_result.success:
                synthesized.selector = healing_result.healed_selector
                synthesized.strategy = healing_result.strategy
                verification = await self.verifier.verify(
                    synthesized.selector,
                    synthesized.strategy
                )
            timing['healing'] = time.time() - heal_start
            
        # Record success/failure for promotion
        if self.use_promotion:
            if verification.ok:
                await self.promotion.record_success(
                    synthesized.selector,
                    synthesized.strategy,
                    self.page.url,
                    {"query": phrase, "confidence": top_result.final_score}
                )
            else:
                await self.promotion.record_failure(
                    synthesized.selector,
                    synthesized.strategy,
                    self.page.url
                )
                
        timing['total'] = time.time() - start_time
        
        return QueryResult(
            success=verification.ok,
            selector=synthesized.selector,
            strategy=synthesized.strategy,
            confidence=top_result.final_score,
            frame_path=verification.frame_path,
            alternatives=synthesized.alternatives,
            verification=verification.to_dict(),
            timing=timing,
            metadata={
                "top_score": top_result.final_score,
                "semantic_score": top_result.semantic_score,
                "heuristic_score": top_result.heuristic_score,
                "promotion_score": top_result.promotion_score,
                "explanation": top_result.explanation,
                "node_name": top_result.node.node_name,
                "total_candidates": len(interactive_nodes)
            }
        )
        
    async def act(
        self,
        step: Union[str, Dict[str, Any]],
        url: Optional[str] = None
    ) -> ActionResult:
        """Execute an action step.
        
        Args:
            step: Action step as string or dict
            url: Optional URL to navigate to
            
        Returns:
            ActionResult with execution details
        """
        if not self._initialized:
            await self.initialize()
            
        start_time = time.time()
        timing = {}
        
        # Parse step
        if isinstance(step, str):
            # Parse natural language step
            action_type, phrase, value = self._parse_step(step)
        else:
            # Dict format
            action_type = step.get('action', 'click')
            phrase = step.get('target', '')
            value = step.get('value')
            
        # Navigate if URL provided
        if url:
            await self.page.goto(url)
            timing['navigation'] = time.time() - start_time
            
        # Query for element
        query_result = await self.query(phrase, wait_stable=True)
        timing['query'] = time.time() - start_time - timing.get('navigation', 0)
        
        if not query_result.success:
            return ActionResult(
                success=False,
                action=action_type,
                selector=query_result.selector,
                value=value,
                waits={},
                frame={"path": query_result.frame_path},
                post_action={},
                timing=timing,
                error="Element not found"
            )
            
        # Map action type
        action_type_enum = self._map_action_type(action_type)
        
        # Execute action
        exec_start = time.time()
        exec_result = await self.executor.execute(
            action_type_enum,
            query_result.selector,
            value=value,
            strategy=query_result.strategy,
            frame_path=query_result.frame_path
        )
        timing['execution'] = time.time() - exec_start
        timing['total'] = time.time() - start_time
        
        return ActionResult(
            success=exec_result.success,
            action=exec_result.action_type,
            selector=exec_result.selector,
            value=exec_result.value,
            waits={
                "before_ms": exec_result.wait_before_ms,
                "after_ms": exec_result.wait_after_ms
            },
            frame={
                "path": query_result.frame_path,
                "url": self.page.url
            },
            post_action=exec_result.post_action,
            timing=timing,
            error=exec_result.error
        )
        
    def _parse_step(self, step: str) -> Tuple[str, str, Optional[Any]]:
        """Parse natural language step.
        
        Args:
            step: Natural language step
            
        Returns:
            Tuple of (action, target, value)
        """
        step_lower = step.lower()
        
        # Detect action type
        if step_lower.startswith('click'):
            action = 'click'
            target = step[5:].strip()
            value = None
        elif step_lower.startswith('type') or step_lower.startswith('enter'):
            action = 'type'
            parts = step.split(' in ', 1)
            if len(parts) == 2:
                value = parts[0].replace('type', '').replace('enter', '').strip().strip('"\'')
                target = parts[1].strip()
            else:
                value = ''
                target = step.replace('type', '').replace('enter', '').strip()
        elif step_lower.startswith('select'):
            action = 'select'
            parts = step.split(' from ', 1)
            if len(parts) == 2:
                value = parts[0].replace('select', '').strip().strip('"\'')
                target = parts[1].strip()
            else:
                value = ''
                target = step.replace('select', '').strip()
        elif step_lower.startswith('check'):
            action = 'check'
            target = step[5:].strip()
            value = None
        elif step_lower.startswith('uncheck'):
            action = 'uncheck'
            target = step[7:].strip()
            value = None
        elif step_lower.startswith('hover'):
            action = 'hover'
            target = step[5:].strip()
            value = None
        else:
            # Default to click
            action = 'click'
            target = step
            value = None
            
        return action, target, value
        
    def _map_action_type(self, action: str) -> ActionType:
        """Map string action to ActionType enum.
        
        Args:
            action: Action string
            
        Returns:
            ActionType enum value
        """
        mapping = {
            'click': ActionType.CLICK,
            'type': ActionType.TYPE,
            'select': ActionType.SELECT,
            'check': ActionType.CHECK,
            'uncheck': ActionType.UNCHECK,
            'hover': ActionType.HOVER,
            'focus': ActionType.FOCUS,
            'clear': ActionType.CLEAR,
            'upload': ActionType.UPLOAD,
            'press': ActionType.PRESS,
            'wait': ActionType.WAIT
        }
        
        return mapping.get(action.lower(), ActionType.CLICK)
        
    async def get_stats(self) -> Dict[str, Any]:
        """Get framework statistics.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            'initialized': self._initialized,
            'headless': self.headless,
            'auto_heal': self.auto_heal,
            'use_promotion': self.use_promotion
        }
        
        if self._initialized:
            if self.session:
                stats['session'] = self.session.get_stats()
            if self.vector_cache:
                stats['cache'] = await self.vector_cache.get_stats()
            if self.element_embedder:
                stats['embedder'] = self.element_embedder.get_cache_stats()
            if self.healer:
                stats['healing'] = self.healer.get_healing_stats()
            if self.promotion:
                stats['promotion'] = await self.promotion.get_stats()
                
        return stats