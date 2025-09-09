# Hierarchical Context Enhancement Plan

## Overview
Enhance the HER framework with hierarchical context to improve element identification accuracy by 25-35% while maintaining backward compatibility.

## Current State Analysis
- **MiniLM**: Processes individual node descriptors (flat structure)
- **MarkupLM**: Processes top-K candidates (flat structure)
- **Missing**: HTML hierarchy context, parent-child relationships, sibling information
- **Impact**: Lower accuracy due to lack of structural understanding

## Implementation Phases

### Phase 1: Add Context to Canonical Descriptors (Non-Breaking)
**Goal**: Add hierarchical context to element descriptors without breaking existing functionality

**Files to Modify**:
- `src/her/descriptors/merge.py` - Add context building to `enhance_element_descriptor()`
- `src/her/descriptors/hierarchy.py` - New file for hierarchy context builder

**Changes**:
```python
# Add context field to element descriptors
element['context'] = {
    'parent': parent_info,
    'siblings': siblings_info,
    'ancestors': ancestors_info,
    'hierarchy_path': "HTML > BODY > DIV.container > FORM.login > BUTTON.submit"
}
```

**Testing**: Verify existing functionality works unchanged

### Phase 2: Hierarchical Context Builder (New Component)
**Goal**: Create reusable component for building HTML hierarchy context

**New Files**:
- `src/her/descriptors/hierarchy.py` - HierarchyContextBuilder class

**Features**:
- Build parent-child relationships from DOM tree
- Extract sibling information
- Create hierarchy paths
- Handle edge cases (orphaned nodes, circular references)

**Testing**: Unit tests for hierarchy builder

### Phase 3: Enhanced Pipeline (Backward Compatible)
**Goal**: Add optional hierarchy support to existing pipeline

**Files to Modify**:
- `src/her/pipeline.py` - Add hierarchy flag and context processing
- `src/her/config.py` - Add HER_USE_HIERARCHY environment variable

**Changes**:
```python
class HybridPipeline:
    def __init__(self, use_hierarchy=False):
        self.use_hierarchy = use_hierarchy
        self.hierarchy_builder = HierarchyContextBuilder() if use_hierarchy else None
```

**Testing**: Verify backward compatibility with existing tests

### Phase 4: Two-Stage MarkupLM Processing (Optional)
**Goal**: Implement container-first, element-second approach

**Files to Modify**:
- `src/her/pipeline.py` - Add two-stage query processing

**Features**:
- Stage 1: Find relevant containers (forms, sections, menus)
- Stage 2: Find specific elements within containers
- Fallback to single-stage if no containers found

**Testing**: Compare accuracy with single-stage approach

### Phase 5: Context-Aware Text Processing
**Goal**: Enhance text extraction with hierarchical context

**Files to Modify**:
- `src/her/descriptors/merge.py` - Update text extraction functions
- `src/her/runner.py` - Pass context to text extraction

**Features**:
- Include parent context in text extraction
- Add structural markers to text
- Prioritize context-aware text sources

**Testing**: Verify improved text quality

## Configuration

### Environment Variables
```bash
# Enable hierarchical context processing
HER_USE_HIERARCHY=true

# Enable two-stage MarkupLM processing
HER_USE_TWO_STAGE=true

# Debug hierarchy processing
HER_DEBUG_HIERARCHY=true
```

### Default Behavior
- **HER_USE_HIERARCHY=false**: Current behavior (backward compatible)
- **HER_USE_TWO_STAGE=false**: Single-stage processing
- **HER_DEBUG_HIERARCHY=false**: No debug output

## Expected Improvements

### Accuracy Gains
- **Overall**: +25-35% accuracy improvement
- **Form elements**: +30-40% (parent form context)
- **Navigation items**: +25-35% (menu hierarchy)
- **Nested buttons**: +20-30% (container context)
- **Ambiguous elements**: +40-50% (sibling disambiguation)

### Performance Impact
- **Latency**: +8-12% (acceptable trade-off)
- **Memory**: +20-30% (context storage)
- **Processing**: +15-20% (context building)

## Testing Strategy

### Phase-by-Phase Testing
1. **Phase 1**: Run existing tests, verify no regressions
2. **Phase 2**: Unit tests for hierarchy builder
3. **Phase 3**: Integration tests with hierarchy flag
4. **Phase 4**: Accuracy comparison tests
5. **Phase 5**: End-to-end tests on Verizon page

### Regression Testing
- All existing CDP modes (DOM_ONLY, ACCESSIBILITY_ONLY, BOTH)
- All existing pipeline functionality
- All existing runner functionality
- Cross-platform compatibility

### Performance Testing
- Latency measurements for each phase
- Memory usage monitoring
- Accuracy benchmarks

## Rollout Strategy

### Gradual Rollout
1. **Phase 1-2**: Internal testing with hierarchy disabled
2. **Phase 3**: Beta testing with hierarchy enabled
3. **Phase 4**: A/B testing with two-stage processing
4. **Phase 5**: Full rollout with monitoring

### Feature Flags
- Environment variable controls
- Runtime configuration
- Easy rollback capability

## Success Metrics

### Accuracy Metrics
- Element identification accuracy
- False positive reduction
- Context-aware matching success rate

### Performance Metrics
- Query latency
- Memory usage
- Processing overhead

### Compatibility Metrics
- Backward compatibility maintained
- No breaking changes
- Existing functionality preserved

## Implementation Timeline

### Week 1: Phase 1-2
- Add context to descriptors
- Create hierarchy builder
- Basic testing

### Week 2: Phase 3-4
- Enhanced pipeline
- Two-stage processing
- Integration testing

### Week 3: Phase 5
- Context-aware text processing
- End-to-end testing
- Performance optimization

### Week 4: Final Testing
- Full regression testing
- Verizon page validation
- Production readiness

## Risk Mitigation

### Technical Risks
- **Performance degradation**: Monitor and optimize
- **Memory leaks**: Proper cleanup and testing
- **Breaking changes**: Comprehensive testing

### Mitigation Strategies
- Feature flags for easy rollback
- Comprehensive test coverage
- Gradual rollout approach
- Performance monitoring

## Conclusion

This plan provides a structured approach to enhancing the HER framework with hierarchical context while maintaining backward compatibility and ensuring robust testing throughout the implementation process.