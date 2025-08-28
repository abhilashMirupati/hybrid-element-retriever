from __future__ import annotations
import json
from typing import Dict
from playwright.sync_api import sync_playwright
from .executor.actions import wait_for_idle
from .bridge.snapshot import get_flat_snapshot
from .locator.verify import verify_locator
from .locator.synthesize import choose_best

def _strict(obj: Dict) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",",":"))

class HybridClient:
    def query(self, phrase: str, url: str) -> Dict:
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True); page = b.new_page(); page.goto(url); wait_for_idle(page)
            candidates = []
            for sel in ["button","input","a","[role=button]","[role=link]"]:
                els = page.query_selector_all(sel)
                for el in els[:100]:
                    try:
                        tag = el.evaluate("(e)=>e.tagName.toLowerCase()")
                        attrs = el.evaluate("""(e)=>{const o={}; for (const a of e.attributes){o[a.name]=a.value}; return o;}""")
                        text = el.inner_text() if el.is_visible() else ""
                        sem = 1.0 if phrase.lower() in (text or "").lower() else 0.0
                        candidates.append({"tag": tag, "attrs": attrs, "text": text, "semantic": sem, "promotion": 0.0})
                    except Exception:
                        continue
            best = choose_best(candidates)
            vr = verify_locator(page, best.get("selector",""), strategy=best.get("strategy","css"), require_unique=True) if best else None
            out = {
                "ok": bool(vr and vr.ok),
                "used_locator": best.get("selector","") if best else "",
                "strategy": best.get("strategy","") if best else "",
                "confidence": float(best.get("score",0.0)) if best else 0.0,
                "verification": vr.__dict__ if vr else {"ok": False, "explanation": "no candidate"},
                "snapshot": get_flat_snapshot(page),
            }
            page.close(); b.close(); return out
    def act(self, step: str, url: str) -> Dict:
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True); page = b.new_page(); page.goto(url); wait_for_idle(page)
            q = self.query(step, url)
            if q["ok"] and q["strategy"] and q["used_locator"]:
                try:
                    target = page.query_selector(q["used_locator"]) if q["strategy"]=="css" else page.query_selector(f"xpath={q['used_locator']}")
                    if target: target.click()
                except Exception:
                    q["ok"] = False
                    if isinstance(q.get("verification"), dict):
                        q["verification"]["explanation"] = "action failed"
            page.close(); b.close(); return q
