"""Main API interface for Hybrid Element Retriever."""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
import time

from .parser.intent import IntentParser
from .session.manager import SessionManager
from .embeddings.query_embedder import QueryEmbedder
from .embeddings.element_embedder import ElementEmbedder
from .rank.heuristics import rank_by_heuristics
from .rank.fusion import RankFusion
from .locator.synthesize import LocatorSynthesizer
from .locator.verify import LocatorVerifier
from .executor.actions import ActionExecutor, ActionResult
from .recovery.self_heal import SelfHealer
from .recovery.promotion import PromotionStore


logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import Page

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    Page = Any
    PLAYWRIGHT_AVAILABLE = False


@dataclass
class QueryResult:
    """Result from element query."""

    selector: str
    score: float
    element: Dict[str, Any]
    explanation: str


class HybridClient:
    """Main client for Hybrid Element Retriever."""

    def __init__(
        self,
        auto_index: bool = True,
        headless: bool = True,
        timeout_ms: int = 30000,
        promotion_enabled: bool = True,
    ):
        """Initialize HybridClient.

        Args:
            auto_index: Enable automatic indexing
            headless: Run browser in headless mode
            timeout_ms: Default timeout in milliseconds
            promotion_enabled: Enable locator promotion
        """
        self.auto_index = auto_index
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.promotion_enabled = promotion_enabled

        # Initialize components
        self.parser = IntentParser()
        self.session_manager = SessionManager(auto_index=auto_index)
        self.query_embedder = QueryEmbedder()
        self.element_embedder = ElementEmbedder()
        self.rank_fusion = RankFusion()
        self.synthesizer = LocatorSynthesizer()
        self.verifier = LocatorVerifier()
        self.executor = ActionExecutor(headless=headless, timeout_ms=timeout_ms)
        self.healer = SelfHealer()
        self.promotion_store = PromotionStore()

        # Current session
        self.current_session_id = "default"
        self._ensure_session()

    def _ensure_session(self) -> None:
        """Ensure a session exists."""
        if not self.session_manager.get_session(self.current_session_id):
            self.session_manager.create_session(
                self.current_session_id, self.executor.page, auto_index=self.auto_index
            )

    def act(self, step: str, url: Optional[str] = None) -> Dict[str, Any]:
        """Execute an action from natural language.

        Args:
            step: Natural language instruction
            url: Optional URL to navigate to first

        Returns:
            JSON-serializable result dictionary
        """
        start_time = time.time()

        # Navigate if URL provided
        if url and self.executor.page:
            self.executor.goto(url)

        # Parse intent
        intent = self.parser.parse(step)
        logger.info(f"Parsed intent: {intent}")

        # Get current session
        session = self.session_manager.get_session(self.current_session_id)

        # Trigger indexing if needed
        if self.executor.page and session:
            descriptors, dom_hash = self.session_manager.index_page(
                self.current_session_id, self.executor.page
            )
        else:
            descriptors = []
            dom_hash = ""

        # Find target element
        candidates = self._find_candidates(intent.target_phrase, descriptors)

        # Generate and verify locators
        best_locator = None
        # used_locator = None  # Not currently used
        n_best = []

        for candidate, score, reasons in candidates[:5]:
            # Synthesize locators
            locators = self.synthesizer.synthesize(candidate)

            # Verify and find unique locator
            verified_locator = self.verifier.find_unique_locator(
                locators, self.executor.page, candidate
            )

            if verified_locator:
                n_best.append(
                    {"locator": verified_locator, "score": score, "reasons": reasons}
                )

                if not best_locator:
                    best_locator = verified_locator
                    # used_locator = verified_locator  # Not currently used

        # Execute action
        result = {
            "status": "failure",
            "method": intent.action,
            "confidence": intent.confidence,
            "dom_hash": dom_hash,
            "framePath": "main",
            "semantic_locator": best_locator,
            "used_locator": None,
            "n_best": n_best[:3],
            "overlay_events": [],
            "retries": {"attempts": 0, "final_method": "none"},
            "explanation": self.parser.explain_intent(intent),
            "duration_ms": 0,
        }

        if best_locator:
            # Try to execute with best locator
            action_result = self._execute_with_recovery(
                intent.action, best_locator, intent.args, candidates
            )

            # Update result
            result["status"] = "success" if action_result.success else "failure"
            result["used_locator"] = action_result.locator
            result["overlay_events"] = action_result.overlay_events
            result["retries"] = {
                "attempts": action_result.retries,
                "final_method": action_result.verification.get("method", "standard"),
            }

            # Handle promotion
            if self.promotion_enabled:
                if action_result.success:
                    self.promotion_store.promote(
                        action_result.locator, context=url or "", boost=0.1
                    )
                else:
                    self.promotion_store.demote(
                        best_locator, context=url or "", penalty=0.05
                    )
        else:
            result["explanation"] += " - No valid locator found"

        # Calculate total duration
        result["duration_ms"] = int((time.time() - start_time) * 1000)

        # Ensure strict JSON output
        return self._clean_json_output(result)

    def query(self, phrase: str, url: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query for element candidates without performing action.

        Args:
            phrase: Search phrase
            url: Optional URL to navigate to first

        Returns:
            List of candidate dictionaries
        """
        # Navigate if URL provided
        if url and self.executor.page:
            self.executor.goto(url)

        # Get current session
        session = self.session_manager.get_session(self.current_session_id)

        # Trigger indexing if needed
        if self.executor.page and session:
            descriptors, dom_hash = self.session_manager.index_page(
                self.current_session_id, self.executor.page
            )
        else:
            descriptors = []
            dom_hash = ""

        # Find candidates
        candidates = self._find_candidates(phrase, descriptors)

        # Format results
        results = []
        for candidate, score, reasons in candidates[:10]:
            # Synthesize locators
            locators = self.synthesizer.synthesize(candidate)

            # Find best verified locator
            best_locator = self.verifier.find_unique_locator(
                locators, self.executor.page, candidate
            )

            results.append(
                {
                    "selector": best_locator or locators[0] if locators else "",
                    "score": score,
                    "element": {
                        "tag": candidate.get("tag"),
                        "text": candidate.get("text"),
                        "role": candidate.get("role"),
                        "name": candidate.get("name"),
                        "id": candidate.get("id"),
                        "classes": candidate.get("classes", []),
                    },
                    "explanation": reasons.get("explanation", ""),
                    "dom_hash": dom_hash,
                    "confidence": score,
                    "rationale": reasons.get("explanation", "")
                }
            )

        # Ensure strict JSON output for each result
        return [self._clean_json_output(r) for r in results]

    def _find_candidates(
        self, phrase: str, descriptors: List[Dict[str, Any]]
    ) -> List[Tuple[Dict[str, Any], float, Dict[str, Any]]]:
        """Find candidate elements for a phrase.

        Args:
            phrase: Search phrase
            descriptors: Element descriptors

        Returns:
            List of (descriptor, score, reasons) tuples
        """
        if not descriptors:
            return []

        # Get session for vector store
        session = self.session_manager.get_session(self.current_session_id)
        if not session:
            return []

        # Semantic search
        query_vec = self.query_embedder.embed(phrase)
        semantic_results = session.vector_store.search(query_vec, top_k=20)

        # Heuristic ranking
        heuristic_results = rank_by_heuristics(descriptors, phrase, top_k=20)

        # Fusion ranking
        context = self.executor.page.url if self.executor.page else ""
        fused_results = self.rank_fusion.fuse(
            semantic_results, heuristic_results, context=context, top_k=10
        )

        return fused_results

    def _execute_with_recovery(
        self,
        action: str,
        locator: str,
        args: Optional[str],
        candidates: List[Tuple[Dict[str, Any], float, Dict[str, Any]]],
    ) -> ActionResult:
        """Execute action with self-healing recovery.

        Args:
            action: Action type
            locator: Primary locator
            args: Action arguments
            candidates: Backup candidates

        Returns:
            ActionResult
        """
        # Try primary locator
        if action == "click":
            result = self.executor.click(locator)
        elif action == "type" and args:
            result = self.executor.fill(locator, args)
        elif action == "select" and args:
            result = self.executor.select(locator, args)
        elif action == "hover":
            result = self.executor.hover(locator)
        else:
            # Unsupported action
            result = ActionResult(
                success=False,
                action=action,
                locator=locator,
                error=f"Unsupported action: {action}",
            )

        # If failed, try self-healing
        if not result.success and self.executor.page:
            healed_locators = self.healer.heal(
                locator, self.executor.page, context={"action": action, "args": args}
            )

            for healed_locator, strategy in healed_locators:
                logger.info(f"Trying healed locator from {strategy}: {healed_locator}")

                # Retry with healed locator
                if action == "click":
                    healed_result = self.executor.click(healed_locator)
                elif action == "type" and args:
                    healed_result = self.executor.fill(healed_locator, args)
                elif action == "select" and args:
                    healed_result = self.executor.select(healed_locator, args)
                elif action == "hover":
                    healed_result = self.executor.hover(healed_locator)
                else:
                    continue

                if healed_result.success:
                    healed_result.verification["healing_strategy"] = strategy

                    # Promote healed locator
                    if self.promotion_enabled:
                        context = self.executor.page.url if self.executor.page else ""
                        self.promotion_store.promote(
                            healed_locator, context=context, boost=0.15
                        )

                    return healed_result

        # If still failed, try alternative candidates
        if not result.success:
            for candidate, _, _ in candidates[1:4]:  # Try next 3 candidates
                alt_locators = self.synthesizer.synthesize(candidate)
                for alt_locator in alt_locators:
                    if action == "click":
                        alt_result = self.executor.click(alt_locator)
                    elif action == "type" and args:
                        alt_result = self.executor.fill(alt_locator, args)
                    elif action == "select" and args:
                        alt_result = self.executor.select(alt_locator, args)
                    elif action == "hover":
                        alt_result = self.executor.hover(alt_locator)
                    else:
                        continue

                    if alt_result.success:
                        alt_result.verification["recovery_method"] = (
                            "alternative_candidate"
                        )
                        return alt_result

        return result

    def _clean_json_output(self, data: Any) -> Any:
        """Ensure strict JSON output with no None or empty values."""
        if isinstance(data, dict):
            return {
                k: self._clean_json_output(v)
                for k, v in data.items()
                if v is not None and v != "" and v != []
            }
        elif isinstance(data, list):
            return [self._clean_json_output(item) for item in data if item is not None]
        else:
            return data
    
    def close(self) -> None:
        """Close browser and clean up resources."""
        self.executor.close()
        logger.info("HybridClient closed")
