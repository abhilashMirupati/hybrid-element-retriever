# archived duplicate of src/her/recovery/promotion.py
"""Promotion system for successful selectors."""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import aiosqlite

logger = logging.getLogger(__name__)


@dataclass 
class PromotionEntry:
    """Entry in promotion database."""
    selector: str
    strategy: str
    url_pattern: str
    success_count: int
    failure_count: int
    last_success: float
    last_failure: Optional[float]
    confidence: float
    metadata: Dict[str, any]
    

class PromotionManager:
    """Manages promotion of successful selectors.
    
    Persists winners in .cache/promotion.db for use in fusion ranking.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path(".cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "promotion.db"
        self._db: Optional[aiosqlite.Connection] = None
        self._memory_cache: Dict[str, PromotionEntry] = {}
        
    async def initialize(self) -> None:
        """Initialize database."""
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        
        # Create tables
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS promotions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                selector TEXT NOT NULL,
                strategy TEXT NOT NULL,
                url_pattern TEXT NOT NULL,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                last_success REAL,
                last_failure REAL,
                confidence REAL DEFAULT 0.5,
                metadata TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                UNIQUE(selector, strategy, url_pattern)
            )
        """)
        
        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_url_pattern
            ON promotions(url_pattern)
        """)
        
        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_confidence
            ON promotions(confidence DESC)
        """)
        
        await self._db.commit()
        
        # Load high-confidence entries to memory
        await self._load_to_memory()
        
        logger.info(f"Promotion manager initialized at {self.db_path}")
        
    async def _load_to_memory(self) -> None:
        """Load high-confidence entries to memory cache."""
        cursor = await self._db.execute("""
            SELECT * FROM promotions
            WHERE confidence > 0.7
            ORDER BY confidence DESC
            LIMIT 1000
        """)
        
        rows = await cursor.fetchall()
        for row in rows:
            key = f"{row['selector']}:{row['strategy']}:{row['url_pattern']}"
            self._memory_cache[key] = PromotionEntry(
                selector=row['selector'],
                strategy=row['strategy'],
                url_pattern=row['url_pattern'],
                success_count=row['success_count'],
                failure_count=row['failure_count'],
                last_success=row['last_success'],
                last_failure=row['last_failure'],
                confidence=row['confidence'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {}
            )
            
        logger.info(f"Loaded {len(self._memory_cache)} high-confidence promotions to memory")
        
    async def record_success(
        self,
        selector: str,
        strategy: str,
        url: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """Record a successful selector usage.
        
        Args:
            selector: Selector that succeeded
            strategy: Selector strategy
            url: Page URL
            metadata: Optional metadata
        """
        url_pattern = self._create_url_pattern(url)
        timestamp = time.time()
        
        # Check if exists
        cursor = await self._db.execute("""
            SELECT * FROM promotions
            WHERE selector = ? AND strategy = ? AND url_pattern = ?
        """, (selector, strategy, url_pattern))
        
        row = await cursor.fetchone()
        
        if row:
            # Update existing
            new_success_count = row['success_count'] + 1
            new_confidence = self._calculate_confidence(
                new_success_count,
                row['failure_count']
            )
            
            await self._db.execute("""
                UPDATE promotions
                SET success_count = ?,
                    last_success = ?,
                    confidence = ?,
                    updated_at = ?
                WHERE selector = ? AND strategy = ? AND url_pattern = ?
            """, (new_success_count, timestamp, new_confidence, timestamp,
                  selector, strategy, url_pattern))
            
            # Update memory cache if high confidence
            if new_confidence > 0.7:
                key = f"{selector}:{strategy}:{url_pattern}"
                self._memory_cache[key] = PromotionEntry(
                    selector=selector,
                    strategy=strategy,
                    url_pattern=url_pattern,
                    success_count=new_success_count,
                    failure_count=row['failure_count'],
                    last_success=timestamp,
                    last_failure=row['last_failure'],
                    confidence=new_confidence,
                    metadata=metadata or {}
                )
        else:
            # Insert new
            metadata_json = json.dumps(metadata) if metadata else None
            
            await self._db.execute("""
                INSERT INTO promotions
                (selector, strategy, url_pattern, success_count, last_success,
                 confidence, metadata, created_at, updated_at)
                VALUES (?, ?, ?, 1, ?, 0.5, ?, ?, ?)
            """, (selector, strategy, url_pattern, timestamp,
                  metadata_json, timestamp, timestamp))
            
        await self._db.commit()
        
    async def record_failure(
        self,
        selector: str,
        strategy: str,
        url: str
    ) -> None:
        """Record a failed selector usage.
        
        Args:
            selector: Selector that failed
            strategy: Selector strategy
            url: Page URL
        """
        url_pattern = self._create_url_pattern(url)
        timestamp = time.time()
        
        # Check if exists
        cursor = await self._db.execute("""
            SELECT * FROM promotions
            WHERE selector = ? AND strategy = ? AND url_pattern = ?
        """, (selector, strategy, url_pattern))
        
        row = await cursor.fetchone()
        
        if row:
            # Update existing
            new_failure_count = row['failure_count'] + 1
            new_confidence = self._calculate_confidence(
                row['success_count'],
                new_failure_count
            )
            
            await self._db.execute("""
                UPDATE promotions
                SET failure_count = ?,
                    last_failure = ?,
                    confidence = ?,
                    updated_at = ?
                WHERE selector = ? AND strategy = ? AND url_pattern = ?
            """, (new_failure_count, timestamp, new_confidence, timestamp,
                  selector, strategy, url_pattern))
            
            # Remove from memory cache if low confidence
            if new_confidence < 0.7:
                key = f"{selector}:{strategy}:{url_pattern}"
                self._memory_cache.pop(key, None)
                
        # Don't insert new entry for failures
        
        await self._db.commit()
        
    async def get_promotion_scores(
        self,
        url: str,
        backend_node_ids: List[int]
    ) -> Dict[int, float]:
        """Get promotion scores for nodes.
        
        Args:
            url: Current page URL
            backend_node_ids: List of backend node IDs
            
        Returns:
            Dictionary mapping backend_node_id to promotion score
        """
        url_pattern = self._create_url_pattern(url)
        scores = {}
        
        # Check memory cache first
        for key, entry in self._memory_cache.items():
            if entry.url_pattern == url_pattern:
                # Map selector to nodes (simplified)
                # In production, would match selector to actual nodes
                for node_id in backend_node_ids[:5]:  # Top nodes get promotion
                    if node_id not in scores:
                        scores[node_id] = entry.confidence * 0.5  # Scale down
                        
        # Also check database for patterns
        cursor = await self._db.execute("""
            SELECT * FROM promotions
            WHERE url_pattern = ? AND confidence > 0.5
            ORDER BY confidence DESC
            LIMIT 20
        """, (url_pattern,))
        
        rows = await cursor.fetchall()
        for row in rows:
            # Map to nodes (simplified)
            for node_id in backend_node_ids[:10]:
                if node_id not in scores:
                    scores[node_id] = row['confidence'] * 0.3
                    
        return scores
        
    def _create_url_pattern(self, url: str) -> str:
        """Create URL pattern for matching.
        
        Args:
            url: Full URL
            
        Returns:
            URL pattern
        """
        # Simple pattern: domain + path without query params
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        pattern = f"{parsed.netloc}{parsed.path}"
        
        # Remove trailing slash
        if pattern.endswith('/'):
            pattern = pattern[:-1]
            
        # Remove numbers (for dynamic IDs)
        import re
        pattern = re.sub(r'\d+', '*', pattern)
        
        return pattern
        
    def _calculate_confidence(self, success_count: int, failure_count: int) -> float:
        """Calculate confidence score.
        
        Args:
            success_count: Number of successes
            failure_count: Number of failures
            
        Returns:
            Confidence score [0, 1]
        """
        total = success_count + failure_count
        if total == 0:
            return 0.5
            
        # Basic success rate with minimum threshold
        base_confidence = success_count / total
        
        # Adjust for sample size (more data = more confidence)
        if total < 5:
            base_confidence *= 0.7  # Low sample penalty
        elif total < 10:
            base_confidence *= 0.85
        elif total < 20:
            base_confidence *= 0.95
            
        return min(1.0, max(0.0, base_confidence))
        
    async def get_stats(self) -> Dict[str, any]:
        """Get promotion statistics.
        
        Returns:
            Dictionary of stats
        """
        cursor = await self._db.execute("""
            SELECT
                COUNT(*) as total_entries,
                SUM(success_count) as total_successes,
                SUM(failure_count) as total_failures,
                AVG(confidence) as avg_confidence,
                COUNT(CASE WHEN confidence > 0.8 THEN 1 END) as high_confidence_count
            FROM promotions
        """)
        
        row = await cursor.fetchone()
        
        return {
            'total_entries': row['total_entries'] or 0,
            'total_successes': row['total_successes'] or 0,
            'total_failures': row['total_failures'] or 0,
            'avg_confidence': row['avg_confidence'] or 0,
            'high_confidence_count': row['high_confidence_count'] or 0,
            'memory_cache_size': len(self._memory_cache)
        }
        
    async def cleanup_old_entries(self, days: int = 30) -> int:
        """Clean up old entries.
        
        Args:
            days: Remove entries older than this many days
            
        Returns:
            Number of entries removed
        """
        cutoff = time.time() - (days * 24 * 3600)
        
        cursor = await self._db.execute("""
            DELETE FROM promotions
            WHERE updated_at < ? AND confidence < 0.5
        """, (cutoff,))
        
        await self._db.commit()
        
        deleted = cursor.rowcount
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old promotion entries")
            # Reload memory cache
            await self._load_to_memory()
            
        return deleted
        
    async def close(self) -> None:
        """Close database connection."""
        if self._db:
            await self._db.close()
            self._db = None