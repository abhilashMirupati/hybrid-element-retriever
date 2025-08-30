Compatibility shims summary

Why these shims were required
- Legacy tests and downstream users expect `HERPipeline` in `her.pipeline` and a helper `resolve_model_paths` under `her.embeddings._resolve`.
- The modern codebase uses `HybridPipeline` as the primary API, and resolver helpers return rich objects rather than the simple dict expected by older tests.
- Without shims, pytest collection fails due to missing symbols and changed signatures.

What was added
- src/her/compat.py:
  - `HERPipeline`: a thin wrapper around `HybridPipeline.process` that returns a deterministic, JSON-serializable dict. It also exposes private methods so tests can patch behavior.
  - `resolve_model_paths()`: calls the modern resolver functions and returns a stable dict for both tasks (`text-embedding`, `element-embedding`), handling missing files gracefully.
- src/her/__init__.py: Exposes `HybridPipeline`, `HERPipeline`, and `resolve_model_paths` via `__all__` and lazy `__getattr__` so legacy imports continue to work.
- pytest.ini: Added `norecursedirs` to avoid collecting archived test trees and build artifacts.

Risk and migration notes
- These shims are intentionally minimal and temporary. They should be removed after consumers migrate to `HybridPipeline` and the new resolver API.
- The shims avoid heavy dependencies and use deterministic fallbacks to keep CI stable.

Verification
- `python -m compileall src`: succeeds.
- `pytest -q`: legacy tests now import without symbol errors, and smoke tests pass. Some functional tests may still require additional mocks or dependency setup, outside the scope of symbol compatibility.

