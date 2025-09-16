# MarkupLM Integration for HER Framework

This document describes the integration of the MarkupLM model into the Hybrid Element Retriever (HER) framework to enhance element ranking based on user queries in no-semantic mode with hierarchical context.

## Overview

The MarkupLM integration provides:

- **Enhanced Snippet Scoring**: Uses MarkupLM model to score HTML snippets based on user queries
- **Hierarchical Context**: Builds parent, sibling, and attribute context for better element understanding
- **XPath Generation**: Generates robust XPath expressions for top-ranked snippets
- **No-Semantic Mode**: Operates without traditional semantic embeddings, using exact matching + MarkupLM ranking

## Architecture

```
User Query → Intent Parsing → Exact Matching → Hierarchical Context Building → MarkupLM Scoring → XPath Generation → Ranked Results
```

### Key Components

1. **MarkupLMSnippetScorer**: Scores HTML snippets using MarkupLM model
2. **MarkupLMHierarchyBuilder**: Builds hierarchical context for elements
3. **MarkupLMNoSemanticMatcher**: Main matcher integrating all components
4. **Enhanced XPath Generator**: Generates multiple XPath strategies with validation

## Installation

### Prerequisites

```bash
pip install transformers==4.46.3 torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0
```

### Model Setup

The MarkupLM model will be automatically downloaded on first use. The default model is:
- `microsoft/markuplm-base-finetuned-websrc`

## Configuration

### Environment Variables

```bash
# Enable no-semantic mode with hierarchy
export HER_USE_SEMANTIC_SEARCH=false
export HER_USE_HIERARCHY=true
export HER_USE_MARKUPLM_NO_SEMANTIC=true

# MarkupLM specific settings
export HER_MARKUPLM_MODEL_NAME="microsoft/markuplm-base-finetuned-websrc"
export HER_MARKUPLM_DEVICE="cpu"  # or "cuda" for GPU
export HER_MARKUPLM_BATCH_SIZE=8

# Debug settings
export HER_DEBUG=true
```

### Configuration Script

Run the configuration script to set up the framework:

```bash
python configure_markuplm_no_semantic.py
```

## Usage

### Basic Usage

```python
from her.locator.markuplm_no_semantic import MarkupLMNoSemanticMatcher

# Create matcher
matcher = MarkupLMNoSemanticMatcher()

# Sample elements
elements = [
    {
        "tag": "button",
        "text": "Apple",
        "attributes": {
            "id": "apple-btn",
            "class": "filter-button",
            "data-testid": "apple-filter"
        },
        "visible": True
    }
]

# Query
query = 'Click on "Apple" filter'
result = matcher.query(query, elements)

print(f"XPath: {result['xpath']}")
print(f"Confidence: {result['confidence']}")
print(f"Strategy: {result['strategy']}")
```

### Advanced Usage with Hierarchical Context

```python
from her.descriptors.markuplm_hierarchy_builder import MarkupLMHierarchyBuilder
from her.embeddings.markuplm_snippet_scorer import MarkupLMSnippetScorer

# Build hierarchical context
builder = MarkupLMHierarchyBuilder()
enhanced_candidates = builder.build_context_for_candidates(candidates, all_elements)

# Score with MarkupLM
scorer = MarkupLMSnippetScorer()
results = scorer.score_snippets(enhanced_candidates, query)

# Generate XPath candidates
from her.utils.xpath_generator import generate_xpath_candidates
xpath_candidates = generate_xpath_candidates(element, hierarchy_context)
```

## API Reference

### MarkupLMSnippetScorer

```python
class MarkupLMSnippetScorer:
    def __init__(self, model_name: str = "microsoft/markuplm-base-finetuned-websrc", 
                 device: str = "cpu", batch_size: int = 8)
    
    def score_snippets(self, candidates: List[Dict[str, Any]], query: str) -> List[SnippetScore]
    def get_top_candidates(self, candidates: List[Dict[str, Any]], query: str, top_k: int = 5) -> List[SnippetScore]
    def is_available(self) -> bool
```

### MarkupLMHierarchyBuilder

```python
class MarkupLMHierarchyBuilder:
    def __init__(self, max_depth: int = 5, max_siblings: int = 5)
    
    def build_context_for_candidates(self, candidates: List[Dict[str, Any]], 
                                   all_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]
    def get_context_summary(self, candidate: Dict[str, Any]) -> Dict[str, Any]
```

### MarkupLMNoSemanticMatcher

```python
class MarkupLMNoSemanticMatcher:
    def __init__(self, model_name: Optional[str] = None)
    
    def query(self, query: str, elements: List[Dict[str, Any]], page=None) -> Dict[str, Any]
    def is_markup_available(self) -> bool
```

## XPath Generation Strategies

The enhanced XPath generator provides multiple strategies:

1. **ID-based**: `//*[@id='element-id']` (highest priority)
2. **Data-testid-based**: `//*[@data-testid='test-id']`
3. **Aria-label-based**: `//*[@aria-label='label']`
4. **Name-based**: `//tag[@name='name']`
5. **Class-based**: `//tag[@class='class']`
6. **Text-based**: `//tag[normalize-space()='text']`
7. **Hierarchical**: Uses parent/sibling context
8. **Combined**: Multiple attributes combined
9. **Generic fallback**: `//tag`

## Testing

### Run Tests

```bash
# Run all MarkupLM integration tests
python -m pytest tests/test_markuplm_integration.py -v

# Run specific test
python -m pytest tests/test_markuplm_integration.py::TestMarkupLMSnippetScorer::test_initialization -v
```

### Run Demonstration

```bash
# Run the full demonstration
python demo_markuplm_integration.py

# Run configuration test
python configure_markuplm_no_semantic.py
```

## Performance Considerations

### Memory Usage

- MarkupLM model requires ~500MB RAM
- Batch processing reduces memory overhead
- Hierarchical context adds ~10-20% memory usage

### Processing Time

- Initial model loading: ~2-3 seconds
- Per-query processing: ~100-500ms (depending on batch size)
- XPath generation: ~1-5ms per candidate

### Optimization Tips

1. Use smaller batch sizes for lower memory usage
2. Limit hierarchical context depth
3. Cache model instances when possible
4. Use GPU acceleration for large-scale processing

## Troubleshooting

### Common Issues

1. **MarkupLM not available**
   - Check if transformers and torch are installed
   - Verify model download completed
   - Check device compatibility

2. **Low confidence scores**
   - Ensure hierarchical context is properly built
   - Check element attributes and text content
   - Verify query matches element characteristics

3. **XPath generation failures**
   - Check element structure and attributes
   - Verify hierarchical context is available
   - Use fallback strategies

### Debug Mode

Enable debug mode for detailed logging:

```bash
export HER_DEBUG=true
export HER_LOG_LEVEL=DEBUG
```

## Examples

### Example 1: Filter Button Selection

```python
# Input elements
elements = [
    {
        "tag": "button",
        "text": "Apple",
        "attributes": {"id": "apple-filter", "class": "filter-btn"},
        "visible": True
    },
    {
        "tag": "button", 
        "text": "Samsung",
        "attributes": {"id": "samsung-filter", "class": "filter-btn"},
        "visible": True
    }
]

# Query
query = 'Click on "Apple" filter'

# Result
{
    "xpath": "//button[@id='apple-filter']",
    "confidence": 0.95,
    "strategy": "markuplm-enhanced",
    "reasons": ["exact_text_match", "interactive_element", "has_id"]
}
```

### Example 2: Search Input Selection

```python
# Input elements
elements = [
    {
        "tag": "input",
        "attributes": {
            "type": "search",
            "placeholder": "Search products...",
            "name": "search"
        },
        "visible": True
    }
]

# Query
query = 'Enter "iPhone" in search field'

# Result
{
    "xpath": "//input[@name='search']",
    "confidence": 0.88,
    "strategy": "markuplm-enhanced",
    "reasons": ["search_input", "has_name", "interactive_element"]
}
```

## Future Enhancements

1. **Model Fine-tuning**: Custom MarkupLM models for specific domains
2. **Multi-language Support**: Support for non-English queries
3. **Advanced Hierarchical Context**: Deeper DOM structure analysis
4. **Performance Optimization**: Model quantization and caching
5. **Integration Testing**: Automated testing with real web pages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This integration follows the same license as the HER framework.