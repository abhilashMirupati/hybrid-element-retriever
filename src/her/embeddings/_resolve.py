from __future__ import annotations
import json, os
from pathlib import Path
from typing import Dict, List, Optional
_MODELS_INFO_NAME='MODEL_INFO.json'
_E5_DIR='e5-small-onnx'
_MARKUPLM_DIR='markuplm-base-onnx'

def _repo_root_from_this_file()->Path:
    return Path(__file__).resolve().parents[2]

def _packaged_models_dir()->Path:
    return _repo_root_from_this_file()/ 'src'/'her'/'models'

def _user_models_dir()->Path:
    return Path.home()/'.her'/'models'

def get_models_base_dirs()->List[Path]:
    env=os.environ.get('HER_MODELS_DIR'); c=[]
    if env: c.append(Path(env).expanduser().resolve())
    c.append(_packaged_models_dir()); c.append(_user_models_dir())
    out,seen=[],set()
    for p in c:
        s=str(p)
        if s not in seen:
            out.append(p); seen.add(s)
    return out

def _read_json(p:Path)->Dict:
    with p.open('r',encoding='utf-8') as f: return json.load(f)

def _find_model_info(base:Path)->Optional[Dict]:
    info=base/_MODELS_INFO_NAME
    if info.is_file():
        try:
            d=_read_json(info)
            if isinstance(d,dict) and 'models' in d: return d
        except Exception: return None
    return None

def _guess_dir_for_name(name:str)->str:
    n=name.lower()
    if n.startswith('e5'): return _E5_DIR
    if 'markuplm' in n: return _MARKUPLM_DIR
    return name

def load_model_info()->Dict[str,Dict]:
    for base in get_models_base_dirs():
        info=_find_model_info(base)
        if info:
            out:Dict[str,Dict]={}
            for m in info.get('models',[]):
                nm=m.get('name');
                if not nm: continue
                rel=m.get('path')
                ap=(base/Path(rel).name).resolve() if rel else (base/_guess_dir_for_name(nm)).resolve()
                out[nm]={'hf_id':m.get('hf_id'),'task':m.get('task'),'path':str(ap)}
            return out
    return {}

def resolve_model_dir(name:str)->Path:
    info=load_model_info()
    if name in info:
        p=Path(info[name]['path'])
        if p.is_dir(): return p
    wanted=_guess_dir_for_name(name)
    for base in get_models_base_dirs():
        cand=(base/wanted).resolve()
        if cand.is_dir(): return cand
    raise FileNotFoundError(f"HER model '{name}' not found. Install with scripts/install_models.sh or scripts/install_models.ps1")

def resolve_file(name:str, filename:str)->Path:
    d=resolve_model_dir(name); f=(d/filename).resolve()
    if not f.is_file(): raise FileNotFoundError(f"File '{filename}' not in model '{name}' at '{d}'")
    return f

def ensure_model_available(name:str)->Path:
    d=resolve_model_dir(name)
    if not (d/'model.onnx').is_file(): raise FileNotFoundError(f"Model '{name}' at '{d}' missing model.onnx")
    return d

E5_SMALL_NAME='e5-small'; MARKUPLM_BASE_NAME='markuplm-base'
__all__=['get_models_base_dirs','load_model_info','resolve_model_dir','resolve_file','ensure_model_available','E5_SMALL_NAME','MARKUPLM_BASE_NAME']
