# Changelog

All notable changes to Hybrid Element Retriever (HER) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-15

### Added
- **Core Features**
  - Natural language to XPath/CSS locator conversion
  - ONNX-optimized E5-small and MarkupLM-base models
  - Deterministic SHA256-based fallback embeddings
  - CDP integration for DOM and accessibility tree extraction
  - Full shadow DOM and iframe support
  - SPA route change detection and re-indexing
  
- **Resilience & Recovery**
  - Self-healing locators with fallback chains
  - Automatic overlay/modal dismissal
  - Occlusion detection via elementFromPoint
  - Post-action verification system
  - Promotion persistence with SQLite storage
  
- **Performance**
  - Two-tier caching (LRU memory + SQLite disk)
  - DOM hash-based delta detection
  - Early-exit fusion scoring
  - Batch embedding support
  
- **Developer Experience**
  - Strict JSON output with no empty fields
  - Comprehensive CLI (`her` command)
  - Python API with type hints
  - Java wrapper via Py4J
  - PowerShell model installation script
  
- **Testing & Quality**
  - 80%+ code coverage requirement
  - Real-world test examples (login, SPA, shadow DOM, iframes)
  - Edge case handling (ambiguous elements, delayed loading)
  - Ubuntu + Windows CI/CD matrix
  
- **Documentation**
  - Production-ready README
  - Comprehensive setup guide
  - Risk assessment with mitigations
  - API reference documentation

### Security
- Input sanitization for XPath/CSS generation
- Secure iframe communication handling
- No hardcoded credentials or secrets

### Performance
- Target: <200ms for simple DOM, <800ms for complex DOM
- Cache hit rate >70% after warm-up
- 100% guaranteed locator uniqueness

## [0.9.0] - 2024-01-01 (Pre-release)

### Added
- Initial MVP implementation
- Basic semantic search functionality
- Playwright integration
- Simple caching mechanism

### Changed
- Refactored from prototype to modular architecture

### Known Issues
- Limited shadow DOM support
- No self-healing capabilities
- Basic error handling

## [0.1.0] - 2023-12-01 (Prototype)

### Added
- Initial proof of concept
- Basic natural language parsing
- Simple XPath generation

---

## Upgrade Guide

### From 0.9.x to 1.0.0

1. **Model Installation Required**
   ```bash
   # New ONNX models must be installed
   bash scripts/install_models.sh
   ```

2. **API Changes**
   - `HybridClient` now returns strict JSON (no None/empty values)
   - New `promotion_enabled` parameter for locator learning
   - `act()` method includes `dismissed_overlays` in response

3. **Configuration**
   - New environment variables: `HER_MODELS_DIR`, `HER_CACHE_DIR`
   - Fusion weights now configurable: α=1.0, β=0.5, γ=0.2

4. **Breaking Changes**
   - Removed deprecated `find_element()` method
   - Changed cache format (clear existing caches)
   - Java wrapper now requires Py4J 0.10.9.7+

## Future Roadmap

### Version 1.1.0 (Planned)
- [ ] Multi-browser support (Firefox, Safari)
- [ ] Visual regression detection
- [ ] Cloud deployment templates
- [ ] REST API server mode

### Version 1.2.0 (Planned)
- [ ] GPT-4 integration for complex queries
- [ ] Distributed caching with Redis
- [ ] Kubernetes operator
- [ ] Performance profiling dashboard

## Support

For migration assistance or bug reports, please open an issue on GitHub:
https://github.com/abhilashMirupati/hybrid-element-retriever/issues