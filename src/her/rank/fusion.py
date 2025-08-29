from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
import json
from .fusion_scorer import FusionScorer  # re-export compatibility

ALPHA_DEFAULT=1.0; BETA_DEFAULT=0.5; GAMMA_DEFAULT=0.2


@dataclass
class FusionConfig:
    alpha: float = ALPHA_DEFAULT
    beta: float = BETA_DEFAULT
    gamma: float = GAMMA_DEFAULT


class RankFusion:
    def __init__(self, config: Optional[FusionConfig] = None, promotion_store_path: Optional[Path] = None) -> None:
        self.config = config or FusionConfig()
        self.promotion_store_path = promotion_store_path
        self.promotions: Dict[str, float] = {}
        if promotion_store_path:
            self._load_promotions()

    # ---- promotion ----
    def _load_promotions(self) -> None:
        p = self.promotion_store_path
        if p and Path(p).is_file():
            try:
                self.promotions = json.loads(Path(p).read_text(encoding='utf-8'))
            except Exception:
                self.promotions = {}
        return self.promotions

    def _save_promotions(self) -> None:
        p = self.promotion_store_path
        if p:
            try:
                Path(p).write_text(json.dumps(self.promotions), encoding='utf-8')
            except Exception:
                pass

    def _get_promotion_key(self, descriptor: Dict[str, Any], context: str) -> str:
        # Prefer stable identifiers
        bid = descriptor.get('backendNodeId') or descriptor.get('id') or descriptor.get('xpath') or descriptor.get('selector') or 'unknown'
        return f"{context}|{bid}"

    def _get_promotion_score(self, descriptor: Dict[str, Any], context: str) -> float:
        try:
            return float(self.promotions.get(self._get_promotion_key(descriptor, context), 0.0))
        except Exception:
            return 0.0

    def promote(self, descriptor: Dict[str, Any], context: str, boost: float = 0.1) -> None:
        k = self._get_promotion_key(descriptor, context)
        self.promotions[k] = float(self.promotions.get(k, 0.0) + boost)
        self._save_promotions()

    def demote(self, descriptor: Dict[str, Any], context: str, penalty: float = 0.1) -> None:
        k = self._get_promotion_key(descriptor, context)
        self.promotions[k] = max(0.0, float(self.promotions.get(k, 0.0) - penalty))
        self._save_promotions()

    # ---- fusion ----
    def fuse(self, semantic_scores: Any, heuristic_scores: Any = None, context: str = 'default', top_k: Optional[int] = None) -> Any:
        # Legacy dict input support
        if isinstance(semantic_scores, dict):
            # Combine per-key lists by summing scores for identical items (by first element)
            accum: Dict[Any, float] = {}
            for _key, pairs in semantic_scores.items():
                try:
                    for item, val in pairs:
                        accum[item] = float(accum.get(item, 0.0) + float(val))
                except Exception:
                    continue
            merged = sorted(accum.items(), key=lambda t: t[1], reverse=True)
            return merged
        # Typed path
        # Create lookup maps
        sem = {id(desc): (desc, s) for desc, s in semantic_scores}
        heu = {id(desc): (desc, s) for desc, s in (heuristic_scores or [])}

        # Combine keys
        keys = set(sem.keys()) | set(heu.keys())
        out: List[Tuple[Dict[str, Any], float, Dict[str, Any]]] = []
        for k in keys:
            d = sem.get(k, (None, 0.0))[0] or heu.get(k, (None, 0.0))[0]
            s_sem = float(sem.get(k, (None, 0.0))[1])
            s_heu = float(heu.get(k, (None, 0.0))[1])
            promo = float(self.promotions.get(self._get_promotion_key(d, context), 0.0))
            fused = self.config.alpha * s_sem + self.config.beta * s_heu + self.config.gamma * promo
            reasons = {
                'semantic_score': s_sem,
                'heuristic_score': s_heu,
                'promotion_score': promo,
                'fused_score': fused,
                'explanation': 'weighted_sum'
            }
            out.append((d, fused, reasons))
        # Stable ordering with deterministic tie-breakers
        out.sort(key=lambda t: (t[1], str(t[0].get('id') or t[0].get('xpath') or t[0].get('selector') or t[0].get('text') or '')), reverse=True)
        # Normalize AFTER fusion
        if out:
            scores = [s for _, s, _ in out]
            mx = max(scores); mn = min(scores); rng = (mx - mn) if mx != mn else 1.0
            normalized: List[Tuple[Dict[str, Any], float, Dict[str, Any]]] = []
            for d, s, r in out:
                ns = (s - mn) / rng
                nr = dict(r); nr['normalized'] = ns
                normalized.append((d, ns, nr))
            out = normalized
        return out[:top_k] if top_k else out

    def rank_candidates(self, candidates: List[Tuple[Dict[str, Any], float, float]]) -> List[Tuple[Dict[str, Any], float, Dict[str, Any]]]:
        semantic_scores = [(d, s_sem) for d, s_sem, _ in candidates]
        heuristic_scores = [(d, s_heu) for d, _, s_heu in candidates]
        return self.fuse(semantic_scores, heuristic_scores, context='default')

    def update_weights(self, alpha: float, beta: float, gamma: float) -> None:
        # Direct set (tests expect exact floats without normalization artifacts)
        self.config.alpha = float(alpha)
        self.config.beta = float(beta)
        self.config.gamma = float(gamma)

    def explain_fusion(self, semantic: float, heuristic: float, promotion: float) -> str:
        fused = self.config.alpha * semantic + self.config.beta * heuristic + self.config.gamma * promotion
        return f"Fusion Score: {fused:.3f} (semantic={semantic:.3f}, heuristic={heuristic:.3f}, promotion={promotion:.3f})"


def fuse(cands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Backward-compatible helper used in older code paths."""
    out = []
    for c in cands:
        s = ALPHA_DEFAULT * float(c.get('semantic', 0.0)) + BETA_DEFAULT * float(c.get('css', 0.0)) + GAMMA_DEFAULT * float(c.get('promotion', 0.0))
        x = dict(c); x['score'] = s; out.append(x)
    out.sort(key=lambda d: (d['score'], str(d.get('selector') or d.get('xpath') or d.get('text') or '')), reverse=True)
    if out:
        mx = max(x['score'] for x in out); mn = min(x['score'] for x in out); rng = (mx - mn) if mx != mn else 1.0
        for x in out:
            x['score'] = (x['score'] - mn) / rng
    return out
