from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from ..core.pipeline import HybridPipeline
from ..recovery.promotion import PromotionStore
from ..recovery.self_heal import SelfHealer

log = logging.getLogger("her.cli")


def _configure_logging(level: str) -> None:
    lvl = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=lvl,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )


def _load_elements_json(path: Path) -> List[Dict[str, Any]]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"ERROR: elements JSON not found: {path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: failed to read elements JSON: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(raw)
    except Exception as e:
        print(f"ERROR: failed to parse JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, list):
        print("ERROR: elements JSON must be a list of element dicts.", file=sys.stderr)
        sys.exit(1)
    return data


def _fake_verify_offline(page: Any, selector: str, *, strategy: str, require_unique: bool = True):
    # Offline verify stub — always ok/unique in CLI mode (no browser context).
    return type("VerifyResult", (), {"ok": True, "unique": True})()


def cmd_rank(args: argparse.Namespace) -> int:
    _configure_logging(args.log_level)

    # Guard: offline requires a JSON of elements
    if not args.elements_json:
        print("ERROR: --elements-json is required in offline mode.", file=sys.stderr)
        return 1

    # Build pipeline
    models_root = Path(args.models_root) if args.models_root else None
    pipeline = HybridPipeline(models_root=models_root)

    # Self-heal wiring
    healer: Optional[SelfHealer] = None
    if args.self_heal:
        store = PromotionStore(path=Path(args.promotions_db) if args.promotions_db else None, use_sqlite=True)
        healer = SelfHealer(store=store, verify_fn=_fake_verify_offline, require_unique=True)

    # Load elements
    elements = _load_elements_json(Path(args.elements_json))

    # Try cache first
    confidence_boost = 0.0
    if healer:
        heal = healer.try_cached(
            page=None,
            query=args.query,
            context_url=args.url or "",
            dom_hash=None,
            extra_context={"frame": args.frame} if args.frame else None,
        )
        if heal.ok and heal.strategy and heal.selector:
            out = {
                "strategy": "cached",
                "confidence": 1.0,
                "results": [{
                    "index": -1,
                    "score": 1.0,
                    "confidence": 1.0,
                    "reason": "cache-hit",
                    "element": {"selector": f"{heal.strategy}={heal.selector}"},
                }],
            }
            print(json.dumps(out, indent=2))
            return 0
        confidence_boost = getattr(heal, "confidence_boost", 0.0)

    # Rank
    top_k = max(1, args.top_k or 10)
    result = pipeline.query(args.query, elements, top_k=top_k)
    if not result.get("results"):
        print(json.dumps(result, indent=2))
        return 2

    # Apply cache boost if present
    if confidence_boost:
        result["results"][0]["confidence"] = float(min(1.0, result["results"][0].get("confidence", 0.0) + confidence_boost))
        result["confidence"] = float(min(1.0, result.get("confidence", 0.0) + confidence_boost))
        if args.explain:
            r0 = result["results"][0]
            r0["reason"] = (r0.get("reason") or "") + "; +cache-boost"

    if not args.explain:
        for r in result["results"]:
            r.pop("reason", None)

    print(json.dumps(result, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="her", description="HER CLI — rank elements for a natural-language query")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("rank", help="Rank elements for a query")
    r.add_argument("--query", required=True, help="Natural language step (e.g., 'click submit')")
    r.add_argument("--url", default="", help="Current page URL (helps self-heal context)")
    r.add_argument("--elements-json", help="Path to JSON with a list of element dicts (offline mode)")
    r.add_argument("--models-root", help="Optional models root folder")
    r.add_argument("--frame", help="Optional frame context")
    r.add_argument("--top-k", type=int, default=10, help="Max results to return")
    r.add_argument("--self-heal", action="store_true", help="Enable promotion cache")
    r.add_argument("--promotions-db", help="SQLite file for promotions (default .her_promotions.sqlite)")
    r.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    r.add_argument("--explain", action="store_true", help="Include scoring reasons")
    r.set_defaults(func=cmd_rank)

    return p


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    rc = args.func(args)
    raise SystemExit(rc)
