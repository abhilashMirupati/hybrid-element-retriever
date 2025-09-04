- **Hidden import risk & mitigation**
  - Risk: Residual imports of legacy modules after renames can cause runtime ImportError.
  - Mitigation: Global grep for exact import patterns; fail-stop if any found; fix to shim path.

- **Signature/contract drift risk & mitigation**
  - Risk: Callers expect `MiniLMEmbedder.embed_query/embed_element` 384-d behavior.
  - Mitigation: Use a shim class with same methods/shape; no mass edits; keep dtype float32.

- **Windows/macOS/Linux path risks & mitigation**
  - Risk: Platform path differences or absolute paths breaking environments.
  - Mitigation: No absolute paths; rely on env-based model root resolver; pure Python I/O unaffected.

- **Model availability risk & mitigation**
  - Risk: Text model not installed or resolver fails, raising at import/use.
  - Mitigation: Shim returns zero-vectors when unavailable; avoids crashes; keeps dims stable.

- **Scope creep risk & mitigation**
  - Risk: Changes bleed past Step-1.
  - Mitigation: Rename only; add shim; restrict edits to imports only if strictly necessary; log all changes.