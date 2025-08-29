from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Optional
class SQLiteKV:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser().resolve(); self.path.parent.mkdir(parents=True, exist_ok=True); self._ensure()
    def _ensure(self) -> None:
        with sqlite3.connect(self.path) as c:
            c.execute('CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v BLOB)'); c.commit()
    def get(self, k: str) -> Optional[bytes]:
        with sqlite3.connect(self.path) as c:
            r = c.execute('SELECT v FROM kv WHERE k=?', (k,)).fetchone(); return r[0] if r else None
    def put(self, k: str, v: bytes) -> None:
        with sqlite3.connect(self.path) as c:
            c.execute('INSERT OR REPLACE INTO kv(k,v) VALUES(?,?)', (k, v)); c.commit()
