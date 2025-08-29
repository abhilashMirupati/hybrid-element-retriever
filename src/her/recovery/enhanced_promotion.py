"""Enhanced promotion system with automatic fallback to cached locators."""

from __future__ import annotations
import sqlite3
import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Any
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class EnhancedPromotionRecord:
    """Enhanced promotion record with additional metadata."""
    locator: str
    context: str
    success_count: int = 0
    failure_count: int = 0
    score: float = 0.0
    last_success: Optional[str] = None  # ISO timestamp
    last_failure: Optional[str] = None
    element_attributes: Dict[str, Any] = None  # Store element attributes for validation
    strategy: str = "css"
    confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            'locator': self.locator,
            'context': self.context,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'score': self.score,
            'last_success': self.last_success,
            'last_failure': self.last_failure,
            'element_attributes': self.element_attributes or {},
            'strategy': self.strategy,
            'confidence': self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EnhancedPromotionRecord':
        """Create from dictionary."""
        return cls(**data)


class EnhancedPromotionStore:
    """Enhanced promotion store with automatic fallback support."""
    
    def __init__(
        self, 
        store_path: Optional[Path|str] = None,
        use_sqlite: bool = True,
        auto_fallback: bool = True,
        min_confidence: float = 0.7
    ):
        self.use_sqlite = use_sqlite
        self.auto_fallback = auto_fallback
        self.min_confidence = min_confidence
        self.cache: Dict[Tuple[str, str], EnhancedPromotionRecord] = {}
        
        if store_path is None:
            store_path = Path('.cache') / ('promotions_enhanced.db' if use_sqlite else 'promotions_enhanced.json')
        
        self.path = Path(store_path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        
        if use_sqlite:
            self._ensure_sqlite()
            self._load_from_sqlite()
        else:
            self._load_from_json()
    
    def _ensure_sqlite(self) -> None:
        """Ensure SQLite schema exists."""
        with sqlite3.connect(self.path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS promotions_v2 (
                    locator TEXT,
                    context TEXT,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    score REAL DEFAULT 0.0,
                    last_success TEXT,
                    last_failure TEXT,
                    element_attributes TEXT,
                    strategy TEXT DEFAULT 'css',
                    confidence REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(locator, context)
                )
            ''')
            
            # Create index for faster lookups
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_promotions_score 
                ON promotions_v2(context, score DESC)
            ''')
            
            conn.commit()
    
    def _load_from_sqlite(self) -> None:
        """Load all records from SQLite into memory cache."""
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('SELECT * FROM promotions_v2')
                
                for row in cursor:
                    attrs = {}
                    if row['element_attributes']:
                        try:
                            attrs = json.loads(row['element_attributes'])
                        except Exception:
                            pass
                    
                    record = EnhancedPromotionRecord(
                        locator=row['locator'],
                        context=row['context'],
                        success_count=row['success_count'],
                        failure_count=row['failure_count'],
                        score=row['score'],
                        last_success=row['last_success'],
                        last_failure=row['last_failure'],
                        element_attributes=attrs,
                        strategy=row['strategy'] or 'css',
                        confidence=row['confidence'] or 0.0
                    )
                    
                    self.cache[(row['locator'], row['context'])] = record
                    
            logger.info(f"Loaded {len(self.cache)} promotion records from SQLite")
            
        except Exception as e:
            logger.error(f"Failed to load from SQLite: {e}")
    
    def _load_from_json(self) -> None:
        """Load from JSON file."""
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding='utf-8'))
                for key, value in data.items():
                    if '|' in key:
                        loc, ctx = key.split('|', 1)
                        self.cache[(loc, ctx)] = EnhancedPromotionRecord.from_dict(value)
                        
                logger.info(f"Loaded {len(self.cache)} promotion records from JSON")
                
            except Exception as e:
                logger.error(f"Failed to load from JSON: {e}")
                self.cache = {}
    
    def record_success(
        self, 
        locator: str, 
        context: str,
        element_attributes: Optional[Dict] = None,
        strategy: str = "css",
        boost: float = 0.1
    ) -> EnhancedPromotionRecord:
        """Record a successful locator usage."""
        key = (locator, context)
        rec = self.cache.get(key)
        
        if not rec:
            rec = EnhancedPromotionRecord(
                locator=locator,
                context=context,
                strategy=strategy
            )
        
        rec.success_count += 1
        rec.last_success = datetime.now().isoformat()
        rec.score = min(1.0, rec.score + boost)
        
        # Update confidence based on success/failure ratio
        total = rec.success_count + rec.failure_count
        if total > 0:
            rec.confidence = rec.success_count / total
        
        # Store element attributes for validation
        if element_attributes:
            rec.element_attributes = element_attributes
        
        self.cache[key] = rec
        self._persist(rec)
        
        logger.debug(
            f"Recorded success for {locator[:30]}... in {context[:30]}... "
            f"(score={rec.score:.2f}, confidence={rec.confidence:.2f})"
        )
        
        return rec
    
    def record_failure(
        self,
        locator: str,
        context: str,
        penalty: float = 0.1
    ) -> EnhancedPromotionRecord:
        """Record a failed locator usage."""
        key = (locator, context)
        rec = self.cache.get(key)
        
        if not rec:
            rec = EnhancedPromotionRecord(locator=locator, context=context)
        
        rec.failure_count += 1
        rec.last_failure = datetime.now().isoformat()
        rec.score = max(0.0, rec.score - penalty)
        
        # Update confidence
        total = rec.success_count + rec.failure_count
        if total > 0:
            rec.confidence = rec.success_count / total
        
        self.cache[key] = rec
        self._persist(rec)
        
        logger.debug(
            f"Recorded failure for {locator[:30]}... in {context[:30]}... "
            f"(score={rec.score:.2f}, confidence={rec.confidence:.2f})"
        )
        
        return rec
    
    def get_best_fallback(
        self,
        context: str,
        min_score: float = 0.5,
        min_confidence: Optional[float] = None
    ) -> Optional[EnhancedPromotionRecord]:
        """Get the best fallback locator for a context."""
        if not self.auto_fallback:
            return None
        
        min_conf = min_confidence or self.min_confidence
        candidates = []
        
        for (loc, ctx), rec in self.cache.items():
            if ctx == context:
                if rec.score >= min_score and rec.confidence >= min_conf:
                    candidates.append(rec)
        
        if not candidates:
            logger.debug(f"No fallback candidates for context: {context[:50]}...")
            return None
        
        # Sort by score * confidence (combined metric)
        candidates.sort(key=lambda r: r.score * r.confidence, reverse=True)
        best = candidates[0]
        
        logger.info(
            f"Found fallback locator: {best.locator[:30]}... "
            f"(score={best.score:.2f}, confidence={best.confidence:.2f})"
        )
        
        return best
    
    def get_fallback_chain(
        self,
        context: str,
        max_fallbacks: int = 3
    ) -> List[EnhancedPromotionRecord]:
        """Get a chain of fallback locators sorted by score."""
        candidates = []
        
        for (loc, ctx), rec in self.cache.items():
            if ctx == context and rec.confidence >= self.min_confidence:
                candidates.append(rec)
        
        # Sort by combined score
        candidates.sort(key=lambda r: r.score * r.confidence, reverse=True)
        
        return candidates[:max_fallbacks]
    
    def validate_element_match(
        self,
        record: EnhancedPromotionRecord,
        current_attributes: Dict[str, Any]
    ) -> float:
        """Validate if current element matches the promoted one."""
        if not record.element_attributes:
            return 0.5  # No attributes to compare
        
        stored = record.element_attributes
        match_score = 0.0
        total_checks = 0
        
        # Check important attributes
        important_attrs = ['id', 'name', 'role', 'type', 'tag']
        for attr in important_attrs:
            if attr in stored and attr in current_attributes:
                total_checks += 1
                if stored[attr] == current_attributes[attr]:
                    match_score += 1.0
        
        # Check classes (partial match)
        if 'classes' in stored and 'classes' in current_attributes:
            total_checks += 1
            stored_classes = set(stored.get('classes', []))
            current_classes = set(current_attributes.get('classes', []))
            if stored_classes and current_classes:
                overlap = len(stored_classes & current_classes)
                match_score += overlap / len(stored_classes)
        
        # Check text similarity (fuzzy match)
        if 'text' in stored and 'text' in current_attributes:
            total_checks += 1
            stored_text = str(stored.get('text', '')).strip()
            current_text = str(current_attributes.get('text', '')).strip()
            if stored_text and current_text:
                # Simple similarity check
                if stored_text == current_text:
                    match_score += 1.0
                elif stored_text in current_text or current_text in stored_text:
                    match_score += 0.5
        
        if total_checks == 0:
            return 0.5
        
        return match_score / total_checks
    
    def _persist(self, record: EnhancedPromotionRecord) -> None:
        """Persist record to storage."""
        if self.use_sqlite:
            self._persist_sqlite(record)
        else:
            self._persist_json()
    
    def _persist_sqlite(self, record: EnhancedPromotionRecord) -> None:
        """Persist to SQLite."""
        try:
            with sqlite3.connect(self.path) as conn:
                attrs_json = json.dumps(record.element_attributes or {})
                
                conn.execute('''
                    INSERT OR REPLACE INTO promotions_v2 
                    (locator, context, success_count, failure_count, score,
                     last_success, last_failure, element_attributes, strategy, confidence, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    record.locator,
                    record.context,
                    record.success_count,
                    record.failure_count,
                    record.score,
                    record.last_success,
                    record.last_failure,
                    attrs_json,
                    record.strategy,
                    record.confidence
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to persist to SQLite: {e}")
    
    def _persist_json(self) -> None:
        """Persist all records to JSON."""
        try:
            data = {}
            for (loc, ctx), rec in self.cache.items():
                key = f"{loc}|{ctx}"
                data[key] = rec.to_dict()
            
            self.path.write_text(json.dumps(data, indent=2), encoding='utf-8')
            
        except Exception as e:
            logger.error(f"Failed to persist to JSON: {e}")
    
    def get_stats(self, context: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about promotions."""
        if context:
            records = [r for (l, c), r in self.cache.items() if c == context]
        else:
            records = list(self.cache.values())
        
        if not records:
            return {
                'total': 0,
                'avg_score': 0.0,
                'avg_confidence': 0.0,
                'high_confidence': 0
            }
        
        total = len(records)
        avg_score = sum(r.score for r in records) / total
        avg_confidence = sum(r.confidence for r in records) / total
        high_confidence = sum(1 for r in records if r.confidence >= self.min_confidence)
        
        return {
            'total': total,
            'avg_score': avg_score,
            'avg_confidence': avg_confidence,
            'high_confidence': high_confidence,
            'top_locators': [
                {'locator': r.locator[:50], 'score': r.score, 'confidence': r.confidence}
                for r in sorted(records, key=lambda x: x.score * x.confidence, reverse=True)[:5]
            ]
        }
    
    def clear(self, context: Optional[str] = None) -> int:
        """Clear promotion records."""
        if context:
            # Clear specific context
            to_remove = [(l, c) for (l, c) in self.cache.keys() if c == context]
            for key in to_remove:
                del self.cache[key]
            
            if self.use_sqlite:
                with sqlite3.connect(self.path) as conn:
                    conn.execute('DELETE FROM promotions_v2 WHERE context = ?', (context,))
                    conn.commit()
            
            count = len(to_remove)
            
        else:
            # Clear all
            count = len(self.cache)
            self.cache.clear()
            
            if self.use_sqlite:
                with sqlite3.connect(self.path) as conn:
                    conn.execute('DELETE FROM promotions_v2')
                    conn.commit()
        
        if not self.use_sqlite:
            self._persist_json()
        
        logger.info(f"Cleared {count} promotion records")
        return count


# Convenience function for backward compatibility
def promote_locator(
    locator: str,
    context: str,
    store: Optional[EnhancedPromotionStore] = None,
    element_attributes: Optional[Dict] = None
) -> EnhancedPromotionRecord:
    """Promote a successful locator."""
    if not store:
        store = EnhancedPromotionStore()
    return store.record_success(locator, context, element_attributes)


__all__ = [
    'EnhancedPromotionRecord',
    'EnhancedPromotionStore',
    'promote_locator'
]