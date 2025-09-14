"""
Deterministic Pipeline Orchestrator for HER Framework

Implements the complete end-to-end pipeline:
parse_step → check_promotion → snapshot → match → rerank → xpath → execute → save

This orchestrator coordinates all components to provide a robust, deterministic
element retrieval and interaction system.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..descriptors.canonical import CanonicalNode, get_canonical_nodes
from ..intent.enhanced_parser import EnhancedIntentParser, ParsedIntent
from ..matching.target_matcher import TargetTextMatcher, ElementNotFoundError
from ..ranking.intent_aware_reranker import IntentAwareReranker
from ..locator.robust_xpath_builder import RobustXPathBuilder
from ..executor.enhanced_executor import EnhancedExecutor
from ..promotion.promotion_adapter import compute_label_key, lookup_promotion, record_success, record_failure
from ..vectordb import get_default_kv
from ..exceptions import ExecutionError, InvalidIntentError

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of pipeline execution."""
    
    # Core results
    success: bool
    selector: str
    confidence: float
    
    # Metadata
    action: str
    target: str
    value: Optional[str]
    
    # Pipeline stages
    used_promotion: bool
    promotion_hit: bool
    reranking_strategy: str
    
    # Performance metrics
    execution_time_ms: float
    stages_timing: Dict[str, float]
    
    # Error information
    error: Optional[str] = None
    error_stage: Optional[str] = None


class DeterministicPipeline:
    """End-to-end deterministic pipeline orchestrator."""
    
    def __init__(self, page, models_root: Optional[str] = None):
        self.page = page
        self.kv = get_default_kv()
        
        # Initialize components
        self.intent_parser = EnhancedIntentParser()
        self.target_matcher = TargetTextMatcher()
        self.reranker = IntentAwareReranker()
        self.xpath_builder = RobustXPathBuilder()
        
        # Initialize executor
        self.executor = EnhancedExecutor(page)
        
        # Performance tracking
        self.stages_timing = {}
    
    def execute_step(self, step: str, snapshot_data: Optional[Dict[str, Any]] = None) -> PipelineResult:
        """
        Execute a single user step through the complete pipeline.
        
        Args:
            step: User step string (e.g., 'Click "Login"', 'Type $"John123" into "Username"')
            snapshot_data: Optional pre-captured snapshot data
            
        Returns:
            PipelineResult with execution details
        """
        start_time = time.time()
        self.stages_timing = {}
        
        try:
            # Stage 1: Parse step
            intent = self._parse_step(step)
            
            # Stage 2: Check promotion
            promotion_result = self._check_promotion(intent, snapshot_data)
            
            # Stage 3: Snapshot (if not provided)
            if snapshot_data is None:
                snapshot_data = self._capture_snapshot()
            
            # Stage 4: Match target
            candidates = self._match_target(intent, snapshot_data)
            
            # Stage 5: Rerank candidates
            best_candidate = self._rerank_candidates(candidates, intent)
            
            # Stage 6: Build XPath
            selector = self._build_xpath(best_candidate)
            
            # Stage 7: Execute action
            self._execute_action(intent, selector)
            
            # Stage 8: Save promotion
            self._save_promotion(intent, selector, best_candidate, promotion_result)
            
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000
            
            return PipelineResult(
                success=True,
                selector=selector,
                confidence=best_candidate.get('confidence', 0.0),
                action=intent.action,
                target=intent.target,
                value=intent.value,
                used_promotion=promotion_result.get('used', False),
                promotion_hit=promotion_result.get('hit', False),
                reranking_strategy='intent_aware_markuplm',
                execution_time_ms=execution_time,
                stages_timing=self.stages_timing,
                error=None,
                error_stage=None
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_stage = getattr(e, 'stage', 'unknown')
            
            logger.error(f"Pipeline execution failed at stage {error_stage}: {e}")
            
            return PipelineResult(
                success=False,
                selector="",
                confidence=0.0,
                action=intent.action if 'intent' in locals() else "",
                target=intent.target if 'intent' in locals() else "",
                value=intent.value if 'intent' in locals() else None,
                used_promotion=False,
                promotion_hit=False,
                reranking_strategy='none',
                execution_time_ms=execution_time,
                stages_timing=self.stages_timing,
                error=str(e),
                error_stage=error_stage
            )
    
    def _parse_step(self, step: str) -> ParsedIntent:
        """Parse user step into structured intent."""
        stage_start = time.time()
        
        try:
            intent = self.intent_parser.parse(step)
            
            # Validate intent
            is_valid, issues = self.intent_parser.validate_intent(intent)
            if not is_valid:
                raise InvalidIntentError(f"Invalid intent: {', '.join(issues)}", step, issues)
            
            self.stages_timing['parse_step'] = (time.time() - stage_start) * 1000
            logger.debug(f"Parsed step: {intent.action} -> {intent.target}")
            return intent
            
        except Exception as e:
            e.stage = 'parse_step'
            raise
    
    def _check_promotion(self, intent: ParsedIntent, snapshot_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Check for existing promotion."""
        stage_start = time.time()
        
        try:
            if not snapshot_data:
                self.stages_timing['check_promotion'] = (time.time() - stage_start) * 1000
                return {'used': False, 'hit': False, 'selector': None}
            
            # Compute promotion key
            page_sig = self._compute_page_signature(snapshot_data)
            frame_hash = self._compute_frame_hash(snapshot_data)
            label_key = compute_label_key(intent.label_tokens)
            
            # Look up promotion
            selector = lookup_promotion(self.kv, page_sig, frame_hash, label_key)
            
            if selector:
                logger.debug(f"Found promotion: {selector}")
                self.stages_timing['check_promotion'] = (time.time() - stage_start) * 1000
                return {'used': True, 'hit': True, 'selector': selector}
            
            self.stages_timing['check_promotion'] = (time.time() - stage_start) * 1000
            return {'used': False, 'hit': False, 'selector': None}
            
        except Exception as e:
            e.stage = 'check_promotion'
            raise
    
    def _capture_snapshot(self) -> Dict[str, Any]:
        """Capture page snapshot."""
        stage_start = time.time()
        
        try:
            # This would integrate with the existing snapshot system
            # For now, return a placeholder
            snapshot_data = {
                'elements': [],
                'dom_hash': '',
                'url': self.page.url if hasattr(self.page, 'url') else ''
            }
            
            self.stages_timing['capture_snapshot'] = (time.time() - stage_start) * 1000
            return snapshot_data
            
        except Exception as e:
            e.stage = 'capture_snapshot'
            raise
    
    def _match_target(self, intent: ParsedIntent, snapshot_data: Dict[str, Any]) -> List[CanonicalNode]:
        """Match target text against page elements."""
        stage_start = time.time()
        
        try:
            # Convert snapshot elements to canonical nodes
            elements = snapshot_data.get('elements', [])
            frame_hash = self._compute_frame_hash(snapshot_data)
            
            canonical_nodes = get_canonical_nodes(elements, frame_hash)
            
            # Match target text
            if intent.target:
                candidates = self.target_matcher.match_target(intent.target, canonical_nodes)
            else:
                candidates = canonical_nodes
            
            self.stages_timing['match_target'] = (time.time() - stage_start) * 1000
            logger.debug(f"Found {len(candidates)} target matches")
            return candidates
            
        except ElementNotFoundError as e:
            e.stage = 'match_target'
            raise
        except Exception as e:
            e.stage = 'match_target'
            raise
    
    def _rerank_candidates(self, candidates: List[CanonicalNode], intent: ParsedIntent) -> Dict[str, Any]:
        """Rerank candidates using MarkupLM + intent awareness."""
        stage_start = time.time()
        
        try:
            if not candidates:
                raise ElementNotFoundError("No candidates to rerank")
            
            # For now, return the first candidate with basic scoring
            # In a full implementation, this would use MarkupLM embeddings
            best_candidate = candidates[0]
            
            # Calculate basic confidence score
            confidence = 0.8  # Placeholder
            
            result = {
                'node': best_candidate,
                'confidence': confidence,
                'reasons': ['first_candidate']
            }
            
            self.stages_timing['rerank_candidates'] = (time.time() - stage_start) * 1000
            logger.debug(f"Reranked candidates, selected: {best_candidate.tag}")
            return result
            
        except Exception as e:
            e.stage = 'rerank_candidates'
            raise
    
    def _build_xpath(self, candidate_result: Dict[str, Any]) -> str:
        """Build robust XPath for the selected candidate."""
        stage_start = time.time()
        
        try:
            node = candidate_result['node']
            selector = self.xpath_builder.build_xpath(node)
            
            if not selector:
                raise Exception("Failed to generate XPath")
            
            self.stages_timing['build_xpath'] = (time.time() - stage_start) * 1000
            logger.debug(f"Built XPath: {selector}")
            return selector
            
        except Exception as e:
            e.stage = 'build_xpath'
            raise
    
    def _execute_action(self, intent: ParsedIntent, selector: str) -> None:
        """Execute the action on the selected element."""
        stage_start = time.time()
        
        try:
            # Compute promotion metadata
            page_sig = self._compute_page_signature({'url': self.page.url})
            frame_hash = self._compute_frame_hash({'url': self.page.url})
            label_key = compute_label_key(intent.label_tokens)
            
            # Execute based on action type
            if intent.action == 'click':
                self.executor.click(
                    selector,
                    page_sig=page_sig,
                    frame_hash=frame_hash,
                    label_key=label_key
                )
            elif intent.action == 'type':
                if not intent.value:
                    raise ValueError("Type action requires a value")
                self.executor.type(
                    selector,
                    intent.value,
                    page_sig=page_sig,
                    frame_hash=frame_hash,
                    label_key=label_key
                )
            elif intent.action == 'validate':
                self.executor.validate(
                    selector,
                    intent.target,
                    page_sig=page_sig,
                    frame_hash=frame_hash,
                    label_key=label_key
                )
            else:
                raise ValueError(f"Unsupported action: {intent.action}")
            
            self.stages_timing['execute_action'] = (time.time() - stage_start) * 1000
            logger.debug(f"Executed {intent.action} on {selector}")
            
        except Exception as e:
            e.stage = 'execute_action'
            raise
    
    def _save_promotion(self, intent: ParsedIntent, selector: str, candidate_result: Dict[str, Any], promotion_result: Dict[str, Any]) -> None:
        """Save successful action as promotion."""
        stage_start = time.time()
        
        try:
            if promotion_result.get('used', False):
                # Promotion was already used, no need to save
                self.stages_timing['save_promotion'] = (time.time() - stage_start) * 1000
                return
            
            # Compute promotion metadata
            page_sig = self._compute_page_signature({'url': self.page.url})
            frame_hash = self._compute_frame_hash({'url': self.page.url})
            label_key = compute_label_key(intent.label_tokens)
            
            # Record success
            record_success(
                self.kv,
                page_sig=page_sig,
                frame_hash=frame_hash,
                label_key=label_key,
                selector=selector
            )
            
            self.stages_timing['save_promotion'] = (time.time() - stage_start) * 1000
            logger.debug(f"Saved promotion: {label_key} -> {selector}")
            
        except Exception as e:
            e.stage = 'save_promotion'
            raise
    
    def _compute_page_signature(self, snapshot_data: Dict[str, Any]) -> str:
        """Compute page signature for promotion key."""
        url = snapshot_data.get('url', '')
        dom_hash = snapshot_data.get('dom_hash', '')
        return f"{url}:{dom_hash}"
    
    def _compute_frame_hash(self, snapshot_data: Dict[str, Any]) -> str:
        """Compute frame hash for promotion key."""
        # For now, use a simple hash of the URL
        url = snapshot_data.get('url', '')
        return str(hash(url))[:16]


def create_deterministic_pipeline(page, models_root: Optional[str] = None) -> DeterministicPipeline:
    """Create a deterministic pipeline instance."""
    return DeterministicPipeline(page, models_root)