from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .parser.intent import IntentParser
from .promotion_adapter import compute_label_key
from .hashing import page_signature
from .pipeline import HybridPipeline
from .browser.snapshot import snapshot_sync

try:
    from playwright.sync_api import sync_playwright
    _PLAYWRIGHT = True
except Exception:  # pragma: no cover
    _PLAYWRIGHT = False


logger = logging.getLogger("her.runner")


@dataclass
class StepResult:
    step: str
    selector: str
    confidence: float
    ok: bool
    info: Dict[str, Any]


class Runner:
    """Run plain-English steps end-to-end using HER pipeline.

    - "Open <url>" navigates
    - Other actions resolve element via snapshot + pipeline, then act
    - Simple self-heal: one retry after re-snapshot
    - Logs JSON per step
    """

    def __init__(self, headless: bool = True) -> None:
        self.headless = headless
        self.intent = IntentParser()
        self.pipeline = HybridPipeline()
        self._page = None
        self._browser = None
        self._playwright = None

    def _ensure_browser(self):
        if not _PLAYWRIGHT:
            return None
        if self._page is None:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=self.headless)
            self._page = self._browser.new_page()
            self._page.set_default_timeout(15000)
        return self._page

    def _close(self) -> None:
        try:
            if self._page:
                self._page.close()
        except Exception:
            pass
        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass
        self._page = None
        self._browser = None
        self._playwright = None

    def _snapshot(self, url: Optional[str] = None) -> Dict[str, Any]:
        page = self._ensure_browser()
        if not _PLAYWRIGHT or not page:
            return {"elements": [], "dom_hash": "", "url": url or ""}
        if url:
            try:
                page.goto(url, wait_until="networkidle")
            except Exception:
                pass
        # Use production snapshotter (isolated browser) to collect rich descriptors
        elements, dom_hash = snapshot_sync(page.url)
        return {"elements": elements, "dom_hash": dom_hash, "url": page.url}

    def _resolve_selector(self, phrase: str, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        elements = snapshot.get("elements", [])
        if not elements:
            return {"selector": "", "confidence": 0.0, "reason": "no-elements"}
        # Promotions: page signature + first frame hash
        ps = page_signature(str(snapshot.get("url", "")))
        frame_hash = None
        for el in elements:
            mh = (el.get("meta") or {}).get("frame_hash")
            if mh:
                frame_hash = mh
                break
        intent = self.intent.parse(phrase)
        label_key = compute_label_key([w for w in (intent.target_phrase or phrase).split()])
        result = self.pipeline.query(
            phrase,
            elements,
            top_k=10,
            page_sig=ps,
            frame_hash=frame_hash,
            label_key=label_key,
        )
        best = (result.get("results") or [])[:1]
        if not best:
            return {"selector": "", "confidence": 0.0, "reason": "no-results"}
        return {
            "selector": best[0].get("selector", ""),
            "confidence": float(result.get("confidence", 0.0)),
            "meta": best[0].get("meta", {}),
            "reasons": best[0].get("reasons", []),
        }

    def _do_action(self, action: str, selector: str, value: Optional[str]) -> None:
        if not _PLAYWRIGHT or not self._page:
            raise RuntimeError("Playwright unavailable for action execution")
        if action == "type" and value is not None:
            self._page.fill(f"xpath={selector}", value)
            return
        # default click for click/select/press
        self._page.locator(f"xpath={selector}").first.click()

    def _validate(self, step: str) -> bool:
        if not _PLAYWRIGHT or not self._page:
            return False
        low = step.lower()
        if low.startswith("validate it landed on ") or low.startswith("validate landed on "):
            expected = step.split(" on ", 1)[1].strip().strip(",")
            try:
                current = self._page.url
            except Exception:
                return False
            return current.split("?")[0].rstrip("/") == expected.rstrip("/")
        return False

    def run(self, steps: List[str]) -> List[StepResult]:
        logs: List[StepResult] = []
        try:
            for raw in steps:
                step = raw.strip()
                if not step:
                    continue
                if step.lower().startswith("open "):
                    url = step.split(" ", 1)[1].strip()
                    self._snapshot(url)
                    logs.append(StepResult(step=step, selector="", confidence=1.0, ok=True, info={"url": url}))
                    logger.info(json.dumps({"step": step, "selector": "", "confidence": 1.0, "ok": True}))
                    continue
                # Validate-only step support
                if step.lower().startswith("validate "):
                    ok = self._validate(step)
                    logs.append(StepResult(step=step, selector="", confidence=1.0, ok=ok, info={}))
                    logger.info(json.dumps({"step": step, "selector": "", "confidence": 1.0, "ok": ok}))
                    if not ok:
                        break
                    continue
                intent = self.intent.parse(step)
                shot = self._snapshot()
                resolved = self._resolve_selector(intent.target_phrase or step, shot)
                selector = resolved.get("selector", "")
                conf = float(resolved.get("confidence", 0.0))
                ok = False
                info: Dict[str, Any] = {"reason": resolved.get("reason"), "reasons": resolved.get("reasons", [])}
                if selector:
                    try:
                        self._do_action(intent.action, selector, intent.args)
                        ok = True
                    except Exception as e1:
                        # Self-heal: re-snapshot and retry once
                        shot = self._snapshot()
                        resolved2 = self._resolve_selector(intent.target_phrase or step, shot)
                        selector2 = resolved2.get("selector", "")
                        if selector2:
                            try:
                                self._do_action(intent.action, selector2, intent.args)
                                selector = selector2
                                conf = float(max(conf, resolved2.get("confidence", 0.0)))
                                ok = True
                            except Exception as e2:  # pragma: no cover
                                info["error"] = str(e2)
                        else:
                            info["error"] = str(e1)
                logs.append(StepResult(step=step, selector=selector, confidence=conf, ok=ok, info=info))
                logger.info(json.dumps({
                    "step": step,
                    "selector": selector,
                    "confidence": conf,
                    "ok": ok,
                    "info": info,
                }, ensure_ascii=False))
        finally:
            self._close()
        return logs


def run_steps(steps: List[str], *, headless: bool = True) -> None:
    """Public entrypoint used by tests. Raises AssertionError if any step fails."""
    runner = Runner(headless=headless)
    results = runner.run(steps)
    failed = [r for r in results if not r.ok]
    if failed:
        f = failed[0]
        raise AssertionError(f"Step failed: {f.step} | selector={f.selector} | info={f.info}")