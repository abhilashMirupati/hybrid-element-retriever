# src/her/recovery/promotion.py
# Promotion & self-healing database for HER.
# On locator failure, HER falls back → retries → if successful,
# persist the winning locator in a promotion DB. Fusion adds γ weight for promoted locators.

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional, Dict


class PromotionDB:
    """
    A persistent SQLite database of promoted locators.
    Schema:
      promotions(
        id INTEGER PRIMARY KEY,
        frame_hash TEXT,
        phrase TEXT,
        locator TEXT,
        strategy TEXT,
        score REAL,
        last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    """

    def __init__(self, db_path: Path | str | None = None) -> None:
        if db_path is None:
            db_path = Path(".cache") / "promotion.db"
        self.db_path = Path(db_path).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS promotions (
                  id INTEGER PRIMARY KEY,
                  frame_hash TEXT NOT NULL,
                  phrase TEXT NOT NULL,
                  locator TEXT NOT NULL,
                  strategy TEXT NOT NULL,
                  score REAL,
                  last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_promotions_phrase_frame ON promotions(phrase, frame_hash)"
            )
            conn.commit()

    def promote(self, frame_hash: str, phrase: str, locator: str, strategy: str, score: float) -> None:
        """
        Insert or replace a winning locator for a given phrase and frame_hash.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO promotions(frame_hash, phrase, locator, strategy, score)
                VALUES (?, ?, ?, ?, ?)
                """,
                (frame_hash, phrase, locator, strategy, score),
            )
            conn.commit()

    def get_promoted(self, frame_hash: str, phrase: str, limit: int = 5) -> List[Dict]:
        """
        Retrieve promoted locators for a given phrase+frame.
        Returns a list of dicts sorted by last_used DESC.
        """
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT locator, strategy, score, last_used
                FROM promotions
                WHERE frame_hash=? AND phrase=?
                ORDER BY last_used DESC
                LIMIT ?
                """,
                (frame_hash, phrase, limit),
            ).fetchall()
        return [
            {"locator": r[0], "strategy": r[1], "score": r[2], "last_used": r[3]} for r in rows
        ]

    def clear(self) -> None:
        """Wipe the promotion DB."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM promotions")
            conn.commit()


# Convenience singleton
_default_db: Optional[PromotionDB] = None


def get_db() -> PromotionDB:
    global _default_db
    if _default_db is None:
        _default_db = PromotionDB()
    return _default_db


def promote_locator(frame_hash: str, phrase: str, locator: str, strategy: str, score: float) -> None:
    get_db().promote(frame_hash, phrase, locator, strategy, score)


def promoted_locators(frame_hash: str, phrase: str, limit: int = 5) -> List[Dict]:
    return get_db().get_promoted(frame_hash, phrase, limit)


def clear_promotions() -> None:
    get_db().clear()


__all__ = [
    "PromotionDB",
    "promote_locator",
    "promoted_locators",
    "clear_promotions",
]
