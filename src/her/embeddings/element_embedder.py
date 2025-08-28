from __future__ import annotations
import hashlib
from typing import List, Sequence
import numpy as np
try:
    import onnxruntime as ort
    from transformers import AutoTokenizer
except Exception:
    ort=None; AutoTokenizer=None  # type: ignore
from ._resolve import ensure_model_available, resolve_file, MARKUPLM_BASE_NAME
class ElementEmbedder:
    def __init__(self)->None:
        self.model_dir=ensure_model_available(MARKUPLM_BASE_NAME)
        self.onnx_path=resolve_file(MARKUPLM_BASE_NAME,'model.onnx')
        self._session=None; self._tokenizer=None
        if ort and AutoTokenizer:
            try:
                self._session=ort.InferenceSession(str(self.onnx_path), providers=['CPUExecutionProvider'])
                self._tokenizer=AutoTokenizer.from_pretrained(self.model_dir)
            except Exception:
                self._session=None; self._tokenizer=None
    def _hash_embed(self, text:str, dim:int=384)->List[float]:
        h=hashlib.sha256(('elm|'+text.strip().lower()).encode('utf-8')).digest()
        rng=np.random.RandomState(int.from_bytes(h[:8],'little',signed=False))
        v=rng.normal(size=dim).astype('float32'); v/= (np.linalg.norm(v)+1e-9); return v.tolist()
    def embed(self, texts:Sequence[str])->List[List[float]]:
        if not texts: return []
        if self._session is None or self._tokenizer is None:
            return [self._hash_embed(t) for t in texts]
        toks=self._tokenizer(list(texts), padding=True, truncation=True, return_tensors='np')
        inputs={k:v.astype('int64') for k,v in toks.items() if k in {'input_ids','attention_mask','token_type_ids'}}
        if 'token_type_ids' not in inputs: inputs['token_type_ids']=np.zeros_like(inputs['input_ids'], dtype='int64')
        outs=self._session.run(None, inputs); x=outs[0] if isinstance(outs, list) else outs
        arr=x.mean(axis=1); arr=arr/(np.linalg.norm(arr,axis=1,keepdims=True)+1e-9); return arr.astype('float32').tolist()
