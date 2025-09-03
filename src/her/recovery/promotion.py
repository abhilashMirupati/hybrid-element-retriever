from __future__ import annotations
import sqlite3
import time
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

DEFAULT_TTL_SEC = 3 * 24 * 3600  # 3 days
DECAY_HALF_LIFE_SEC = 24 * 3600  # 1 day half-life


@dataclass
class PromotionRecord:
    locator: str
    context: str
    success_count: int = 0
    failure_count: int = 0
    score: float = 0.0
    ts: float = 0.0
    ttl_sec: float = float(DEFAULT_TTL_SEC)

    def is_fresh(self, now: Optional[float] = None) -> bool:
        n = now or time.time()
        ttl = float(self.ttl_sec or DEFAULT_TTL_SEC)
        return (n - float(self.ts or 0.0)) <= ttl

    def decayed_score(self, now: Optional[float] = None) -> float:
        n = now or time.time()
        age = max(0.0, n - float(self.ts or 0.0))
        if age <= 0.0:
            return float(self.score or 0.0)
        return float(self.score or 0.0) * math.pow(2.0, -age / float(DECAY_HALF_LIFE_SEC))


class PromotionStore:
    def __init__(self, path: Optional[Path] = None, use_sqlite: bool = True, default_ttl_sec: float = DEFAULT_TTL_SEC):
        self.path = Path(path) if path else Path(".her_promotions.sqlite")
        self.use_sqlite = bool(use_sqlite)
        self.default_ttl_sec = float(default_ttl_sec)
        self._cache: Dict[Tuple[str, str], PromotionRecord] = {}
        if self.use_sqlite:
            self._ensure_sqlite()
            self._load_from_sqlite()

    def _ensure_sqlite(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS promotions (
                    locator TEXT NOT NULL,
                    context TEXT NOT NULL,
                    success_count INTEGER NOT NULL DEFAULT 0,
                    failure_count INTEGER NOT NULL DEFAULT 0,
                    score REAL NOT NULL DEFAULT 0.0,
                    ts REAL NOT NULL DEFAULT 0.0,
                    ttl_sec REAL NOT NULL DEFAULT ?
                );
                """,
                (self.default_ttl_sec,),
            )
            c.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_promotions ON promotions (locator, context);")
            c.commit()

    def _load_from_sqlite(self) -> None:
        with sqlite3.connect(self.path) as c:
            rows = c.execute(
                "SELECT locator, context, success_count, failure_count, score, ts, ttl_sec FROM promotions"
            ).fetchall()
        for (locator, context, succ, fail, score, ts, ttl) in rows:
            self._cache[(locator, context)] = PromotionRecord(
                locator=locator,
                context=context,
                success_count=int(succ or 0),
                failure_count=int(fail or 0),
                score=float(score or 0.0),
                ts=float(ts or 0.0),
                ttl_sec=float(ttl or self.default_ttl_sec),
            )

    def _persist(self, rec: PromotionRecord) -> None:
        if not self.use_sqlite:
            return
        with sqlite3.connect(self.path) as c:
            c.execute(
                """
                INSERT INTO promotions (locator, context, success_count, failure_count, score, ts, ttl_sec)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(locator, context) DO UPDATE SET
                    success_count=excluded.success_count,
                    failure_count=excluded.failure_count,
                    score=excluded.score,
                    ts=excluded.ts,
                    ttl_sec=excluded.ttl_sec
                """,
                (rec.locator, rec.context, rec.success_count, rec.failure_count, rec.score, rec.ts, rec.ttl_sec),
            )
            c.commit()

    def record_success(self, locator: str, context: str, boost: float = 0.10) -> PromotionRecord:
        key = (locator, context)
        rec = self._cache.get(key) or PromotionRecord(locator=locator, context=context, ttl_sec=self.default_ttl_sec)
        rec.success_count += 1
        rec.score = float(rec.score + float(boost))
        rec.ts = time.time()
        self._cache[key] = rec
        self._persist(rec)
        return rec

    def record_failure(self, locator: str, context: str, penalty: float = 0.05) -> PromotionRecord:
        key = (locator, context)
        rec = self._cache.get(key) or PromotionRecord(locator=locator, context=context, ttl_sec=self.default_ttl_sec)
        rec.failure_count += 1
        rec.score = max(0.0, float(rec.score - float(penalty)))
        rec.ts = time.time()
        self._cache[key] = rec
        self._persist(rec)
        return rec

    def purge_expired(self, now: Optional[float] = None) -> int:
        n = now or time.time()
        to_delete = []
        for (locator, context), rec in self._cache.items():
            ttl = float(rec.ttl_sec or self.default_ttl_sec)
            if (n - float(rec.ts or 0.0)) > ttl:
                to_delete.append((locator, context))
        for k in to_delete:
            self._cache.pop(k, None)
        if self.use_sqlite and to_delete:
            with sqlite3.connect(self.path) as c:
                c.executemany("DELETE FROM promotions WHERE locator=? AND context=?", to_delete)
                c.commit()
        return len(to_delete)

    def clear(self, context: Optional[str] = None) -> int:
        if context is None:
            count = len(self._cache)
            self._cache.clear()
            if self.use_sqlite:
                with sqlite3.connect(self.path) as c:
                    c.execute("DELETE FROM promotions")
                    c.commit()
            return count
        keys = [k for k in self._cache if k[1] == context]
        for k in keys:
            self._cache.pop(k, None)
        if self.use_sqlite:
            with sqlite3.connect(self.path) as c:
                c.execute("DELETE FROM promotions WHERE context=?", (context,))
                c.commit()
        return len(keys)

    def top_for_context(
        self,
        context: str,
        limit: int = 3,
        min_score: float = 0.0,
        now: Optional[float] = None,
    ) -> List[PromotionRecord]:
        n = now or time.time()
        self.purge_expired(now=n)
        rows = [rec for (loc, ctx), rec in self._cache.items() if ctx == context and rec.is_fresh(now=n)]
        rows.sort(
            key=lambda r: (
                -float(r.decayed_score(n)),
                -int(r.success_count or 0),
                int(r.failure_count or 0),
                -float(r.ts or 0.0),
            )
        )
        out: List[PromotionRecord] = []
        for r in rows:
            if r.decayed_score(n) >= float(min_score):
                out.append(r)
            if len(out) >= int(limit):
                break
        return out

    def dump(self) -> List[Dict[str, float]]:
        return [asdict(v) for v in self._cache.values()]
