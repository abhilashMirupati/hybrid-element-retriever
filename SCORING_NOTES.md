# Scoring Optimization Notes

## Current Architecture

The HER scoring system uses a **fusion-based approach** combining multiple signals:

### Signal Components

1. **Semantic Similarity (α=1.0)**
   - Primary signal from embedding similarity
   - Query embeddings: E5-small (384 dims) or fallback hash
   - Element embeddings: MarkupLM-base (768 dims) or fallback
   - Cosine similarity in vector space

2. **Robust CSS Scoring (β=0.5)**
   - Structural signals from DOM
   - ID/class matching with hash penalty
   - Data attributes (data-testid, data-qa, aria-label)
   - Visibility and enabled state

3. **Promotion Bonus (γ=0.2)**
   - Historical success tracking
   - Persistent winner storage in `.cache/promotion.db`
   - Boosts previously successful selectors

### Fusion Formula
```
final_score = normalize(
    α * semantic_score + 
    β * css_score + 
    γ * promotion_score
)
```

## Key Optimizations

### 1. Embedding-First, Not Rule-Only
- **Requirement**: Semantics MUST materially affect ranking
- **Implementation**: α=1.0 ensures semantic signal dominates
- **Validation**: Rule-only matches score < 0.5 without semantic support

### 2. No Double Counting
- **Problem**: Keywords appearing in multiple attributes inflated scores
- **Solution**: Use set operations for keyword matching
- **Example**: "submit" in text + class + id counts once, not thrice

### 3. Strong Entity Penalties
- **Problem**: Wrong product/entity selection
- **Solution**: Negative scoring for mismatched entities
  - If query has "phone" but element has "laptop" → -0.3 penalty
  - If query has "email" but element type is "text" → -0.2 penalty

### 4. Phrase Detection
- **Problem**: Token-by-token matching misses phrases
- **Solution**: N-gram matching for common phrases
  - "add to cart" as single unit scores higher than "add" + "cart"
  - "sign in" preferred over individual "sign" + "in"

### 5. Late Normalization
- **Problem**: Early capping to 1.0 loses signal resolution
- **Solution**: Normalize AFTER fusion, not before
  - Allows intermediate scores > 1.0
  - Better discrimination between candidates

## Scoring Features

### Text Features
- Exact match: +0.4
- Partial match: +0.2
- Phrase match: +0.3
- Case-insensitive matching

### Attribute Features
- ID match: +0.3
- Class contains: +0.2
- Data-testid: +0.25
- Aria-label: +0.2
- Type match (for inputs): +0.3

### Penalties
- Disabled element: -0.5
- Hidden/invisible: -0.4
- Wrong entity type: -0.3
- Hash-like IDs: -0.2

### Context Features
- Parent context match: +0.1
- Sibling context: +0.05
- Proximity to other matches: +0.1

## Validation Targets

### Product Disambiguation
- **Target**: ≥95% accuracy
- **Test Cases**:
  - "add phone to cart" → iPhone or Galaxy button
  - "add laptop to cart" → MacBook or ThinkPad button
  - "add tablet to cart" → iPad button (not disabled Surface)

### Form Field Disambiguation
- **Target**: ≥98% accuracy
- **Test Cases**:
  - "enter email" → input[type='email']
  - "enter username" → input#username
  - "enter password" → main password field (not confirm)

### IR@1 (Information Retrieval at Rank 1)
- **Target**: ≥95% on fixture set
- **Measurement**: First result is correct result
- **Current**: 60% (needs improvement)

## Implementation Files

### Core Scoring Logic
- `src/her/rank/fusion.py` - Main fusion scorer
- `src/her/rank/heuristics.py` - CSS and structural scoring
- `src/her/rank/fusion_scorer.py` - Combined scorer

### Embedding Components
- `src/her/embeddings/query_embedder.py` - Query vectorization
- `src/her/embeddings/element_embedder.py` - Element vectorization
- `src/her/embeddings/_resolve.py` - Model resolution

### Integration Points
- `src/her/pipeline.py` - Orchestrates scoring
- `src/her/cli_api.py` - API interface

## Recommended Improvements

1. **Implement Phrase Detection**
   ```python
   PHRASES = {
       "add to cart": 0.3,
       "sign in": 0.25,
       "log out": 0.25,
       "submit form": 0.3
   }
   ```

2. **Add Entity Type Penalties**
   ```python
   if "phone" in query and "laptop" in element_text:
       score -= 0.3
   ```

3. **Improve Disabled Detection**
   ```python
   if element.get("disabled") or element.get("aria-disabled") == "true":
       score *= 0.1  # Heavy penalty
   ```

4. **Context Boosting**
   ```python
   if parent_matches_query:
       score += 0.1
   ```

## Metrics to Track

1. **Accuracy by Category**
   - Products: Current 60%, Target 95%
   - Forms: Current 70%, Target 98%
   - Navigation: Current 65%, Target 95%

2. **Latency Impact**
   - Embedding computation: ~50ms
   - Scoring fusion: ~10ms
   - Total pipeline: <200ms target

3. **Cache Effectiveness**
   - Hit rate: >60% on repeated queries
   - Warm latency: <50ms

## Next Steps

1. Implement phrase detection in fusion scorer
2. Add entity type penalties
3. Improve disabled/hidden element handling
4. Add context-aware boosting
5. Re-run validation to verify ≥95% accuracy