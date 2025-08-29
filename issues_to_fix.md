# Issues to Fix

## 1. Thread Safety
- [ ] Cache is not thread-safe
- [ ] Need to add locks for concurrent access

## 2. Embeddings Issue
- [ ] Currently using random fallback embeddings
- [ ] Need to properly implement MiniLM and MarkupLM
- [ ] Models are mentioned but not actually loading

## 3. Untested Features (Need Mock HTML)
- [ ] Frame support
- [ ] Shadow DOM handling
- [ ] SPA detection
- [ ] Network idle detection
- [ ] Loading overlays

## 4. Implementation Gaps
- [ ] MiniLM model not actually loaded
- [ ] MarkupLM model not actually loaded
- [ ] Embeddings are just random vectors

Let's fix each one...