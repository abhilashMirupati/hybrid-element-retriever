from __future__ import annotations
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import json


@dataclass
class PromotionRecord:
    locator: str
    context: str
    success_count: int = 0
    failure_count: int = 0
    score: float = 0.0


class PromotionStore:
    def __init__(self, store_path: Optional[Path|str] = None, use_sqlite: bool = True) -> None:
        self.use_sqlite = use_sqlite
        self.cache: Dict[Tuple[str,str], PromotionRecord] = {}
        if store_path is None:
            store_path = Path('.cache') / ('promotions.db' if use_sqlite else 'promotions.json')
        self.path = Path(store_path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if use_sqlite:
            self._ensure_sqlite()
        else:
            if self.path.exists():
                try:
                    data = json.loads(self.path.read_text(encoding='utf-8'))
                    for k, v in data.items():
                        loc, ctx = k.split('|',1)
                        self.cache[(loc,ctx)] = PromotionRecord(locator=loc, context=ctx, **v)
                except Exception:
                    self.cache = {}

    def _ensure_sqlite(self) -> None:
        with sqlite3.connect(self.path) as c:
            c.execute('CREATE TABLE IF NOT EXISTS promotions(locator TEXT, context TEXT, success INTEGER, failure INTEGER, score REAL, PRIMARY KEY(locator,context))')
            c.commit()

    def record_success(self, locator: str, context: str, boost: float = 0.1) -> PromotionRecord:
        return self.promote(locator, context, boost)

    def record_failure(self, locator: str, context: str, penalty: float = 0.1) -> PromotionRecord:
        return self.demote(locator, context, penalty)

    def promote(self, locator: str, context: str, boost: float = 0.1) -> PromotionRecord:
        key = (locator, context)
        rec = self.cache.get(key) or PromotionRecord(locator=locator, context=context)
        rec.success_count += 1
        rec.score = float(rec.score + boost)
        self.cache[key] = rec
        self._persist(rec)
        return rec

    def demote(self, locator: str, context: str, penalty: float = 0.1) -> PromotionRecord:
        key = (locator, context)
        rec = self.cache.get(key) or PromotionRecord(locator=locator, context=context)
        rec.failure_count += 1
        rec.score = max(0.0, float(rec.score - penalty))
        self.cache[key] = rec
        self._persist(rec)
        return rec

    def get_score(self, locator: str, context: str) -> float:
        rec = self.cache.get((locator, context))
        if rec:
            return float(rec.score)
        # Load from disk if sqlite
        if self.use_sqlite and self.path.exists():
            with sqlite3.connect(self.path) as c:
                row = c.execute('SELECT score FROM promotions WHERE locator=? AND context=?', (locator, context)).fetchone()
                return float(row[0]) if row else 0.0
        return 0.0

    def get_promotion_score(self, locator: str, context: str) -> float:
        return self.get_score(locator, context)

    def get_best_locators(self, context: str, top_k: int = 3) -> List[Tuple[str, float]]:
        items = [(loc, rec.score) for (loc, ctx), rec in self.cache.items() if ctx == context]
        items.sort(key=lambda t: t[1], reverse=True)
        return items[:top_k]

    def _persist(self, rec: PromotionRecord) -> None:
        if self.use_sqlite:
            with sqlite3.connect(self.path) as c:
                c.execute('INSERT OR REPLACE INTO promotions(locator,context,success,failure,score) VALUES(?,?,?,?,?)', (rec.locator, rec.context, rec.success_count, rec.failure_count, rec.score))
                c.commit()
        else:
            # Write entire cache
            data = {f"{loc}|{ctx}": {
                'success_count': r.success_count,
                'failure_count': r.failure_count,
                'score': r.score,
            } for (loc, ctx), r in self.cache.items()}
            self.path.write_text(json.dumps(data), encoding='utf-8')

    def clear(self, context: Optional[str] = None) -> int:
        if context is None:
            count = len(self.cache)
            self.cache.clear()
            if self.use_sqlite:
                with sqlite3.connect(self.path) as c:
                    c.execute('DELETE FROM promotions'); c.commit()
            else:
                if self.path.exists():
                    self.path.unlink()
            return count
        # Remove only records for context
        keys = [k for k in self.cache if k[1] == context]
        for k in keys:
            self.cache.pop(k, None)
        if self.use_sqlite and self.path.exists():
            with sqlite3.connect(self.path) as c:
                c.execute('DELETE FROM promotions WHERE context=?', (context,)); c.commit()
        else:
            self._persist(PromotionRecord(locator='', context=context))  # trigger rewrite
        return len(keys)

    def get_stats(self) -> Dict[str, float|int|List[Tuple[str,float]]]:
        total_records = len(self.cache)
        total_successes = sum(r.success_count for r in self.cache.values())
        total_failures = sum(r.failure_count for r in self.cache.values())
        avg = (sum(r.score for r in self.cache.values()) / total_records) if total_records else 0.0
        top = sorted([(r.locator, r.score) for r in self.cache.values()], key=lambda t: t[1], reverse=True)[:5]
        success_rate = (total_successes / (total_successes + total_failures)) if (total_successes + total_failures) else 0.0
        return {
            'total_records': total_records,
            'total_successes': total_successes,
            'total_failures': total_failures,
            'avg_score': avg,
            'success_rate': success_rate,
            'top_performers': top,
        }


# Backward-compatible simple helpers
def promote_locator(locator: str, context: str, *args, **kwargs) -> None:
    PromotionStore(use_sqlite=True).promote(locator, context, boost=float(kwargs.get('score', 0.1)))

def get_promotion_score(locator: str, context: str) -> float:
    return PromotionStore(use_sqlite=True).get_score(locator, context)

