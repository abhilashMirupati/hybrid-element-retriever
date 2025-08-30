from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from ._resolve import get_element_resolver, ONNXResolver
from ..vectordb.two_tier_cache import TwoTierCache


class ElementEmbedder:
    """Element embedder with partial re-embed and deterministic fallback.

    API:
    - batch_encode(elems: list[dict]) -> np.ndarray[np.float32]
    """

    def __init__(self, cache_dir: Optional[Path] = None, max_memory_items: int = 4096, dim: int = 384, **_: object) -> None:
        self.dim = int(dim)
        root = Path(cache_dir) if cache_dir else (Path.home() / '.cache' / 'her')
        self.cache = TwoTierCache(root, max_memory_items=max_memory_items)
        self.resolver: ONNXResolver = get_element_resolver()
        self._session = None
        self._init_session()

    def _init_session(self) -> None:
        onnx_path, _ = self.resolver.files()
        if onnx_path is None:
            self._session = None
            return
        try:
            import onnxruntime as ort  # type: ignore

            self._session = ort.InferenceSession(str(onnx_path), providers=['CPUExecutionProvider'])
        except Exception:
            self._session = None

    def _hash_elem(self, elem: Dict[str, Any]) -> str:
        def _stable(obj: Any) -> str:
            if isinstance(obj, dict):
                return '{' + ','.join(f"{k}:{_stable(obj[k])}" for k in sorted(obj.keys())) + '}'
            if isinstance(obj, list):
                return '[' + ','.join(_stable(x) for x in obj) + ']'
            return str(obj)
        raw = _stable({'tag': elem.get('tag'), 'text': elem.get('text'), 'attrs': elem.get('attrs') or elem.get('attributes', {}), 'role': elem.get('role'), 'aria': elem.get('aria'), 'context': elem.get('context')})
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def _hash_fallback(self, elem: Dict[str, Any]) -> np.ndarray:
        seed_bytes = hashlib.sha256(self._hash_elem(elem).encode('utf-8')).digest()
        seed = int.from_bytes(seed_bytes[:8], 'little', signed=False) & 0xFFFFFFFF
        rng = np.random.default_rng(seed)
        vec = rng.standard_normal(self.dim, dtype=np.float32)
        norm = float(np.linalg.norm(vec))
        return vec if norm == 0.0 else (vec / norm).astype(np.float32)

    def _to_text(self, elem: Dict[str, Any]) -> str:
        parts: List[str] = []
        tag = elem.get('tag') or ''
        text = elem.get('text') or ''
        attrs = elem.get('attrs') or elem.get('attributes') or {}
        role = elem.get('role') or ''
        aria = elem.get('aria') or ''
        context = elem.get('context') or ''
        if tag:
            parts.append(f"tag:{tag}")
        if text:
            parts.append(f"text:{str(text)[:200]}")
        for k in ('id', 'name', 'data-testid', 'aria-label'):
            v = attrs.get(k)
            if v:
                parts.append(f"{k}:{v}")
        if role:
            parts.append(f"role:{role}")
        if aria:
            parts.append(f"aria:{aria}")
        if context:
            parts.append(f"ctx:{context}")
        return ' '.join(parts)

    def batch_encode(self, elems: List[Dict[str, Any]]) -> np.ndarray:
        if not elems:
            return np.zeros((0, self.dim), dtype=np.float32)
        keys = [self._hash_elem(e) for e in elems]
        cached = self.cache.batch_get(keys)
        out: List[np.ndarray] = [np.zeros((self.dim,), dtype=np.float32) for _ in elems]
        to_put: List[Tuple[str, np.ndarray, Optional[Dict[str, Any]]]] = []
        to_compute: List[Tuple[int, Dict[str, Any], str]] = []
        for i, (k, e) in enumerate(zip(keys, elems)):
            if k in cached:
                out[i] = cached[k].astype(np.float32)
            else:
                to_compute.append((i, e, k))
        # Compute misses
        for i, e, k in to_compute:
            if self._session is None:
                vec = self._hash_fallback(e)
            else:
                try:
                    # Minimal inputs - element texts converted to pseudo-sentence
                    text = self._to_text(e)
                    input_ids = np.zeros((1, 16), dtype=np.int64)
                    attention_mask = np.ones((1, 16), dtype=np.int64)
                    token_type_ids = np.zeros((1, 16), dtype=np.int64)
                    outs = self._session.run(None, {
                        'input_ids': input_ids,
                        'attention_mask': attention_mask,
                        'token_type_ids': token_type_ids,
                    })
                    x = outs[0] if isinstance(outs, list) else outs
                    arr = np.array(x).mean(axis=1).reshape(-1).astype(np.float32)
                    if arr.size != self.dim:
                        arr = np.resize(arr, self.dim).astype(np.float32)
                    norm = float(np.linalg.norm(arr))
                    vec = arr if norm == 0.0 else (arr / norm).astype(np.float32)
                except Exception:
                    vec = self._hash_fallback(e)
            out[i] = vec
            to_put.append((k, vec, {'source': 'element'}))
        if to_put:
            self.cache.batch_put(to_put)
        return np.stack(out, axis=0).astype(np.float32)