from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict
class PromotionDB:
    def __init__(self, db_path: Optional[str|Path]=None)->None:
        if db_path is None: db_path=Path('.cache')/'promotion.db'
        self.db_path=Path(db_path).expanduser().resolve(); self.db_path.parent.mkdir(parents=True, exist_ok=True); self._ensure_schema()
    def _ensure_schema(self)->None:
        with sqlite3.connect(self.db_path) as c:
            c.execute('CREATE TABLE IF NOT EXISTS promotions(id INTEGER PRIMARY KEY, frame_hash TEXT NOT NULL, phrase TEXT NOT NULL, locator TEXT NOT NULL, strategy TEXT NOT NULL, score REAL, last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_phrase_frame ON promotions(phrase, frame_hash)'); c.commit()
    def promote(self, frame_hash:str, phrase:str, locator:str, strategy:str, score:float)->None:
        with sqlite3.connect(self.db_path) as c:
            c.execute('INSERT INTO promotions(frame_hash,phrase,locator,strategy,score) VALUES(?,?,?,?,?)',(frame_hash,phrase,locator,strategy,score)); c.commit()
    def get_promoted(self, frame_hash:str, phrase:str, limit:int=5)->List[Dict]:
        with sqlite3.connect(self.db_path) as c:
            rows=c.execute('SELECT locator,strategy,score,last_used FROM promotions WHERE frame_hash=? AND phrase=? ORDER BY last_used DESC LIMIT ?',(frame_hash,phrase,limit)).fetchall()
        return [{'locator':r[0],'strategy':r[1],'score':r[2],'last_used':r[3]} for r in rows]
    def clear(self)->None:
        with sqlite3.connect(self.db_path) as c:
            c.execute('DELETE FROM promotions'); c.commit()
_default: Optional[PromotionDB]=None

def get_db()->PromotionDB:
    global _default
    if _default is None: _default=PromotionDB()
    return _default

def promote_locator(frame_hash:str, phrase:str, locator:str, strategy:str, score:float)->None:
    get_db().promote(frame_hash, phrase, locator, strategy, score)

def promoted_locators(frame_hash:str, phrase:str, limit:int=5)->List[Dict]:
    return get_db().get_promoted(frame_hash, phrase, limit)

def clear_promotions()->None:
    get_db().clear()
__all__=['PromotionDB','promote_locator','promoted_locators','clear_promotions']
