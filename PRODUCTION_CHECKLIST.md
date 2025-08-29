# HER Production Readiness Checklist

## Phase 1: Component Flow Validation

### 1. Cold Start Flow
- [ ] Snapshot DOM + Accessibility tree
- [ ] Generate MarkupLM embeddings for all elements
- [ ] Store in cache for reuse
- [ ] Verify first-run performance <3s

### 2. Incremental Updates
- [ ] Detect SPA delta via DOM hash
- [ ] Identify new/changed elements only
- [ ] Embed only delta elements
- [ ] Merge with existing embeddings

### 3. User Intent Parsing
- [ ] MiniLM processes natural language
- [ ] Extract action + arguments
- [ ] Pass NLP scoring tests
- [ ] Handle ambiguous queries

### 4. Semantic Matching & Scoring
- [ ] Remove rule-based logic
- [ ] Implement fusion scoring
- [ ] No double-counting
- [ ] No premature capping
- [ ] Test: "add phone to cart" → phone (not laptop)
- [ ] Test: "enter email" → email input (not username)
- [ ] Test: "submit form" → submit button

### 5. Retrieval Pipeline
- [ ] MiniLM generates shortlist
- [ ] MarkupLM reranks candidates
- [ ] Generate best XPath
- [ ] Provide fallback XPaths

### 6. Execution Flows
- [ ] Handle wait states
- [ ] Detect/dismiss loaders
- [ ] Handle popups/modals
- [ ] Support frames
- [ ] Handle stale DOM
- [ ] Support shadow DOM

### 7. Caching
- [ ] Snapshot reuse when DOM unchanged
- [ ] Invalidation on DOM change
- [ ] Memory + persistent cache
- [ ] Cache hit rate >80%

### 8. Edge Cases
- [ ] Unicode inputs
- [ ] Empty queries
- [ ] Duplicate labels
- [ ] Long text truncation
- [ ] Special characters

### 9. CI & Production
- [ ] All tests green
- [ ] Documentation aligned with code
- [ ] Redundant files removed
- [ ] Performance benchmarks met