# Bridge module: rank fusion (markup + heuristics)
from typing import Any, Dict, List


def fuse(candidates: List[Dict[str, Any]], intent: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Import your real rerank here (e.g., markuplm + heuristics)
    from ..embeddings.element_embedder import score_with_markup  # example
    scored = [dict(c, score=score_with_markup(c, intent)) for c in candidates]
    return sorted(scored, key=lambda x: x["score"], reverse=True)
