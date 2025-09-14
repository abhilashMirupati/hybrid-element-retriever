"""Promotion store for caching successful selectors."""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class PromotionStore:
    """SQLite-based store for caching successful selectors."""
    
    def __init__(self, path: Optional[Path] = None, use_sqlite: bool = True):
        """Initialize the promotion store.
        
        Args:
            path: Path to SQLite database file
            use_sqlite: Whether to use SQLite (True) or in-memory storage (False)
        """
        self.use_sqlite = use_sqlite
        if use_sqlite:
            self.db_path = path or Path(".her_promotions.sqlite")
            self._init_db()
        else:
            self._cache: Dict[str, Any] = {}
    
    def _init_db(self) -> None:
        """Initialize SQLite database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS promotions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                url TEXT,
                dom_hash TEXT,
                strategy TEXT NOT NULL,
                selector TEXT NOT NULL,
                confidence REAL,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(query, url, dom_hash, strategy, selector)
            )
        """)
        conn.commit()
        conn.close()
    
    def store(self, query: str, strategy: str, selector: str, 
              confidence: float = 1.0, url: str = "", 
              dom_hash: str = "", context: Optional[Dict[str, Any]] = None) -> None:
        """Store a successful selector.
        
        Args:
            query: The query that led to this selector
            strategy: The strategy used (e.g., 'xpath', 'css')
            selector: The successful selector
            confidence: Confidence score
            url: URL where this worked
            dom_hash: Hash of DOM when this worked
            context: Additional context
        """
        if self.use_sqlite:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO promotions 
                (query, url, dom_hash, strategy, selector, confidence, context)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (query, url, dom_hash, strategy, selector, confidence, 
                  json.dumps(context) if context else None))
            conn.commit()
            conn.close()
        else:
            key = f"{query}:{url}:{dom_hash}"
            self._cache[key] = {
                "strategy": strategy,
                "selector": selector,
                "confidence": confidence,
                "context": context
            }
    
    def lookup(self, query: str, url: str = "", dom_hash: str = "") -> List[Dict[str, Any]]:
        """Look up cached selectors for a query.
        
        Args:
            query: The query to look up
            url: URL context
            dom_hash: DOM hash context
            
        Returns:
            List of cached selectors
        """
        if self.use_sqlite:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT strategy, selector, confidence, context
                FROM promotions
                WHERE query = ? AND (url = ? OR url = '') AND (dom_hash = ? OR dom_hash = '')
                ORDER BY confidence DESC, created_at DESC
            """, (query, url, dom_hash))
            results = []
            for row in cursor.fetchall():
                results.append({
                    "strategy": row[0],
                    "selector": row[1],
                    "confidence": row[2],
                    "context": json.loads(row[3]) if row[3] else None
                })
            conn.close()
            return results
        else:
            key = f"{query}:{url}:{dom_hash}"
            if key in self._cache:
                return [self._cache[key]]
            return []
    
    def clear(self) -> None:
        """Clear all cached promotions."""
        if self.use_sqlite:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("DELETE FROM promotions")
            conn.commit()
            conn.close()
        else:
            self._cache.clear()