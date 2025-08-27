"""Promotion system for successful locators."""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import sqlite3
import logging

logger = logging.getLogger(__name__)

DEFAULT_STORE_PATH = Path.home() / ".cache" / "her" / "promotions.db"


@dataclass
class PromotionRecord:
    """Record of a promoted locator."""

    locator: str
    context: str
    success_count: int = 0
    failure_count: int = 0
    score: float = 0.0
    last_used: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PromotionStore:
    """Persistent storage for locator promotions."""

    def __init__(self, store_path: Optional[Path] = None, use_sqlite: bool = True):
        self.store_path = store_path or DEFAULT_STORE_PATH
        self.use_sqlite = use_sqlite
        self.cache: Dict[str, PromotionRecord] = {}

        if use_sqlite:
            self._init_sqlite()
        else:
            self._init_json()

        self._load_cache()

    def _init_sqlite(self) -> None:
        """Initialize SQLite database."""
        self.store_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self.store_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS promotions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                locator TEXT NOT NULL,
                context TEXT NOT NULL,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                score REAL DEFAULT 0.0,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                UNIQUE(locator, context)
            )
        """
        )

        conn.commit()
        conn.close()

        logger.info(f"Initialized SQLite promotion store at {self.store_path}")

    def _init_json(self) -> None:
        """Initialize JSON file storage."""
        json_path = self.store_path.with_suffix(".json")
        json_path.parent.mkdir(parents=True, exist_ok=True)

        if not json_path.exists():
            with open(json_path, "w") as f:
                json.dump({}, f)

        logger.info(f"Initialized JSON promotion store at {json_path}")

    def _load_cache(self) -> None:
        """Load promotions into memory cache."""
        if self.use_sqlite:
            self._load_from_sqlite()
        else:
            self._load_from_json()

    def _load_from_sqlite(self) -> None:
        """Load promotions from SQLite."""
        conn = sqlite3.connect(str(self.store_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT locator, context, success_count, failure_count, 
                   score, last_used, metadata
            FROM promotions
        """
        )

        for row in cursor.fetchall():
            key = self._make_key(row[0], row[1])
            metadata = json.loads(row[6]) if row[6] else {}

            self.cache[key] = PromotionRecord(
                locator=row[0],
                context=row[1],
                success_count=row[2],
                failure_count=row[3],
                score=row[4],
                last_used=(
                    datetime.fromisoformat(row[5])
                    if isinstance(row[5], str)
                    else datetime.now()
                ),
                metadata=metadata,
            )

        conn.close()
        logger.info(f"Loaded {len(self.cache)} promotions from SQLite")

    def _load_from_json(self) -> None:
        """Load promotions from JSON file."""
        json_path = self.store_path.with_suffix(".json")

        try:
            with open(json_path, "r") as f:
                data = json.load(f)

            for key, record_data in data.items():
                self.cache[key] = PromotionRecord(
                    locator=record_data["locator"],
                    context=record_data["context"],
                    success_count=record_data.get("success_count", 0),
                    failure_count=record_data.get("failure_count", 0),
                    score=record_data.get("score", 0.0),
                    last_used=datetime.fromisoformat(
                        record_data.get("last_used", datetime.now().isoformat())
                    ),
                    metadata=record_data.get("metadata", {}),
                )

            logger.info(f"Loaded {len(self.cache)} promotions from JSON")
        except Exception as e:
            logger.warning(f"Failed to load promotions from JSON: {e}")

    def _make_key(self, locator: str, context: str) -> str:
        """Create cache key from locator and context."""
        return f"{context}::{locator}"

    def promote(
        self,
        locator: str,
        context: str = "",
        boost: float = 0.1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PromotionRecord:
        """Promote a successful locator.

        Args:
            locator: The successful locator
            context: Context (e.g., URL or action)
            boost: Score increase amount
            metadata: Optional metadata to store

        Returns:
            Updated promotion record
        """
        key = self._make_key(locator, context)

        if key in self.cache:
            record = self.cache[key]
            record.success_count += 1
            record.score = min(1.0, record.score + boost)
            record.last_used = datetime.now()
            if metadata:
                record.metadata.update(metadata)
        else:
            record = PromotionRecord(
                locator=locator,
                context=context,
                success_count=1,
                score=boost,
                metadata=metadata or {},
            )
            self.cache[key] = record

        self._persist_record(record)

        logger.info(
            f"Promoted locator: {locator[:50]}... "
            f"(score: {record.score:.3f}, successes: {record.success_count})"
        )

        return record

    def demote(
        self, locator: str, context: str = "", penalty: float = 0.05
    ) -> PromotionRecord:
        """Demote a failed locator.

        Args:
            locator: The failed locator
            context: Context
            penalty: Score decrease amount

        Returns:
            Updated promotion record
        """
        key = self._make_key(locator, context)

        if key in self.cache:
            record = self.cache[key]
            record.failure_count += 1
            record.score = max(0.0, record.score - penalty)
            record.last_used = datetime.now()
        else:
            record = PromotionRecord(
                locator=locator, context=context, failure_count=1, score=0.0
            )
            self.cache[key] = record

        self._persist_record(record)

        logger.info(
            f"Demoted locator: {locator[:50]}... "
            f"(score: {record.score:.3f}, failures: {record.failure_count})"
        )

        return record

    def get_score(self, locator: str, context: str = "") -> float:
        """Get promotion score for a locator.

        Args:
            locator: The locator
            context: Context

        Returns:
            Promotion score (0.0 to 1.0)
        """
        key = self._make_key(locator, context)
        if key in self.cache:
            return self.cache[key].score
        return 0.0

    def get_best_locators(
        self, context: str = "", top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Get best promoted locators for a context.

        Args:
            context: Context to filter by
            top_k: Number of top locators to return

        Returns:
            List of (locator, score) tuples
        """
        candidates = []

        for key, record in self.cache.items():
            if context in record.context:
                candidates.append((record.locator, record.score))

        # Sort by score descending
        candidates.sort(key=lambda x: x[1], reverse=True)

        return candidates[:top_k]

    def _persist_record(self, record: PromotionRecord) -> None:
        """Persist a promotion record to storage."""
        if self.use_sqlite:
            self._persist_to_sqlite(record)
        else:
            self._persist_to_json()

    def _persist_to_sqlite(self, record: PromotionRecord) -> None:
        """Persist record to SQLite."""
        conn = sqlite3.connect(str(self.store_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO promotions 
            (locator, context, success_count, failure_count, score, last_used, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                record.locator,
                record.context,
                record.success_count,
                record.failure_count,
                record.score,
                record.last_used.isoformat(),
                json.dumps(record.metadata),
            ),
        )

        conn.commit()
        conn.close()

    def _persist_to_json(self) -> None:
        """Persist all records to JSON."""
        json_path = self.store_path.with_suffix(".json")

        data = {}
        for key, record in self.cache.items():
            data[key] = {
                "locator": record.locator,
                "context": record.context,
                "success_count": record.success_count,
                "failure_count": record.failure_count,
                "score": record.score,
                "last_used": record.last_used.isoformat(),
                "metadata": record.metadata,
            }

        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)

    def clear(self, context: Optional[str] = None) -> int:
        """Clear promotions.

        Args:
            context: Optional context to clear (None clears all)

        Returns:
            Number of records cleared
        """
        if context:
            # Clear specific context
            keys_to_remove = [k for k, r in self.cache.items() if context in r.context]
            for key in keys_to_remove:
                del self.cache[key]
            count = len(keys_to_remove)
        else:
            # Clear all
            count = len(self.cache)
            self.cache.clear()

        # Persist changes
        if self.use_sqlite:
            conn = sqlite3.connect(str(self.store_path))
            cursor = conn.cursor()
            if context:
                cursor.execute(
                    "DELETE FROM promotions WHERE context LIKE ?", (f"%{context}%",)
                )
            else:
                cursor.execute("DELETE FROM promotions")
            conn.commit()
            conn.close()
        else:
            self._persist_to_json()

        logger.info(f"Cleared {count} promotion records")
        return count

    def get_stats(self) -> Dict[str, Any]:
        """Get promotion statistics.

        Returns:
            Statistics dictionary
        """
        if not self.cache:
            return {
                "total_records": 0,
                "avg_score": 0.0,
                "total_successes": 0,
                "total_failures": 0,
                "success_rate": 0.0,
            }

        total_successes = sum(r.success_count for r in self.cache.values())
        total_failures = sum(r.failure_count for r in self.cache.values())
        total_attempts = total_successes + total_failures

        return {
            "total_records": len(self.cache),
            "avg_score": sum(r.score for r in self.cache.values()) / len(self.cache),
            "total_successes": total_successes,
            "total_failures": total_failures,
            "success_rate": (
                total_successes / total_attempts if total_attempts > 0 else 0.0
            ),
            "top_performers": self.get_best_locators(top_k=3),
        }
