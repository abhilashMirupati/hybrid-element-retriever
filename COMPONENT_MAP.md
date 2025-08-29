# HER Framework - Complete Component Map

## 🎯 Core Modules (Entry Points)

### 1. **cli_api.py** (Main API)
- **Classes**: `HybridClient`, `QueryResult`, `ActionResult`
- **Purpose**: Primary Python API for natural language web automation
- **Usage**: External applications import and use `HybridClient`

### 2. **cli.py** (CLI Interface)
- **Functions**: `main()`, `handle_cache_command()`
- **Purpose**: Command-line interface for the framework
- **Usage**: `her act "click button"` commands

### 3. **gateway_server.py** (Java Bridge)
- **Classes**: `PythonGateway`
- **Purpose**: Py4J gateway for Java integration
- **Usage**: Enables Java/Selenium projects to use HER

## 🧠 Natural Language Processing

### 4. **parser/intent.py**
- **Classes**: `Intent`, `IntentParser`
- **Purpose**: Parses natural language commands into structured intents
- **Usage**: Extracts action type and target from user input

## 🌐 Browser Integration

### 5. **bridge/cdp_bridge.py**
- **Classes**: `DOMSnapshot`
- **Functions**: `wait_for_dom_stable()`, `get_flattened_document()`
- **Purpose**: Chrome DevTools Protocol integration
- **Usage**: Captures DOM and accessibility tree

### 6. **bridge/snapshot.py**
- **Functions**: `capture_snapshot()`, `get_flat_snapshot()`
- **Purpose**: DOM snapshot creation
- **Usage**: Creates structured representation of page state

## 📊 Session Management

### 7. **session/manager.py**
- **Classes**: `SessionState`, `SessionManager`
- **Purpose**: Basic session and DOM management
- **Usage**: Tracks page state and indexes elements

### 8. **session/enhanced_manager.py**
- **Classes**: `EnhancedSessionState`, `EnhancedSessionManager`
- **Purpose**: Advanced session features (SPA tracking, incremental updates)
- **Usage**: Production-grade session management

## 🔍 Element Discovery & Ranking

### 9. **embeddings/query_embedder.py**
- **Classes**: `QueryEmbedder`
- **Purpose**: Converts natural language queries to embeddings
- **Usage**: Semantic search for elements

### 10. **embeddings/element_embedder.py**
- **Classes**: `ElementEmbedder`
- **Purpose**: Converts DOM elements to embeddings
- **Usage**: Semantic matching with queries

### 11. **rank/fusion.py**
- **Classes**: `FusionConfig`, `RankFusion`
- **Purpose**: Combines multiple ranking signals
- **Usage**: Merges semantic, heuristic, and promotion scores

### 12. **rank/fusion_scorer.py**
- **Classes**: `ScoreType`, `ElementScore`, `FusionScorer`
- **Purpose**: Advanced scoring system
- **Usage**: Multi-factor element scoring

### 13. **rank/heuristics.py**
- **Functions**: `heuristic_score()`, `rank_by_heuristics()`
- **Purpose**: Rule-based element scoring
- **Usage**: Non-ML fallback scoring

## 🎯 Locator Generation

### 14. **locator/synthesize.py**
- **Classes**: `LocatorSynthesizer`
- **Purpose**: Base locator generation
- **Usage**: Creates XPath/CSS selectors

### 15. **locator/simple_synthesize.py**
- **Classes**: `LocatorSynthesizer` (extended)
- **Purpose**: Multiple strategy locator generation
- **Usage**: 10+ strategies for robust selectors

### 16. **locator/verify.py**
- **Classes**: `VerificationResult`
- **Purpose**: Validates locator uniqueness
- **Usage**: Ensures locators identify single element

### 17. **locator/enhanced_verify.py**
- **Classes**: `EnhancedVerificationResult`, `PopupHandler`
- **Purpose**: Advanced verification with popup handling
- **Usage**: Production-grade verification

## 🔧 Self-Healing & Recovery

### 18. **recovery/self_heal.py**
- **Classes**: `HealingStrategy`, `SelfHealer`
- **Purpose**: Basic self-healing mechanisms
- **Usage**: Fallback when locators fail

### 19. **recovery/enhanced_self_heal.py**
- **Classes**: `HealingStatus`, `HealingResult`, `HealingStrategy` (base)
- **Strategies**: `RelaxExactMatchStrategy`, `AttributeFallbackStrategy`, etc.
- **Purpose**: Advanced self-healing with multiple strategies
- **Usage**: Production-grade recovery

### 20. **recovery/promotion.py**
- **Classes**: `PromotionRecord`, `PromotionStore`
- **Purpose**: Basic locator promotion
- **Usage**: Tracks successful locators

### 21. **recovery/enhanced_promotion.py**
- **Classes**: `EnhancedPromotionRecord`, `EnhancedPromotionStore`
- **Purpose**: SQLite-backed promotion with confidence scores
- **Usage**: Production persistence

## ⚙️ Action Execution

### 22. **executor/actions.py**
- **Classes**: `ActionError`, `ActionResult`, `ActionExecutor`
- **Purpose**: Browser action execution
- **Usage**: Performs click, type, select actions

### 23. **executor/session.py**
- **Classes**: `Session`
- **Purpose**: Execution session management
- **Usage**: Manages browser context

## 🎭 Complex Scenario Handlers

### 24. **handlers/complex_scenarios.py**
- **Classes**: `WaitStrategy`, `StaleElementHandler`, `DynamicContentHandler`
- **Classes**: `FrameHandler`, `ShadowDOMHandler`, `SPANavigationHandler`
- **Purpose**: Edge case handling
- **Usage**: Handles modern web complexity

## 💾 Caching System

### 25. **cache/two_tier.py**
- **Classes**: `CacheEntry`, `LRUCache`, `SQLiteCache`, `TwoTierCache`
- **Purpose**: Performance optimization
- **Usage**: In-memory + persistent caching

### 26. **embeddings/cache.py**
- **Classes**: `EmbeddingCache`
- **Purpose**: Embedding-specific caching
- **Usage**: Caches computed embeddings

## 🔧 Utilities

### 27. **utils.py** / **utils/__init__.py**
- **Functions**: `sha1_of()`, `flatten()`, `sanitize_text()`, `truncate_text()`
- **Purpose**: Common utility functions
- **Usage**: Throughout the framework

### 28. **utils/cache.py**
- **Classes**: `LRUCache` (generic)
- **Purpose**: Generic caching utility
- **Usage**: Template for caching

### 29. **utils/config.py**
- **Classes**: `Config`
- **Purpose**: Configuration management
- **Usage**: Framework settings

### 30. **config.py**
- **Functions**: `get_models_dir()`, `get_cache_dir()`
- **Purpose**: Path configuration
- **Usage**: Directory management

## 🗃️ Data Storage

### 31. **vectordb/faiss_store.py**
- **Classes**: `InMemoryVectorStore`
- **Purpose**: Vector similarity search
- **Usage**: Semantic matching (optional)

### 32. **vectordb/sqlite_cache.py**
- **Classes**: `SQLiteKV`
- **Purpose**: Key-value storage
- **Usage**: Persistent caching

## 📝 Descriptors

### 33. **descriptors.py** / **descriptors/__init__.py**
- **Classes**: `ElementDescriptor`
- **Functions**: `normalize_descriptor()`
- **Purpose**: Element representation
- **Usage**: Standardized element format

### 34. **descriptors/merge.py**
- **Functions**: `merge_dom_ax()`, `extract_text()`
- **Purpose**: DOM + Accessibility tree merging
- **Usage**: Combines multiple data sources

## 🔌 ML Integration

### 35. **embeddings/_resolve.py**
- **Functions**: Model resolution utilities
- **Purpose**: ML model loading (optional)
- **Usage**: Handles ONNX/Transformer models

## Component Count Summary:
- **Core Modules**: 3
- **NLP Components**: 1
- **Browser Integration**: 2
- **Session Management**: 2
- **Discovery & Ranking**: 5
- **Locator Generation**: 4
- **Self-Healing**: 4
- **Action Execution**: 2
- **Complex Handlers**: 1 (with 6 sub-handlers)
- **Caching**: 2
- **Utilities**: 4
- **Data Storage**: 2
- **Descriptors**: 2
- **ML Integration**: 1

**Total**: 35 primary components across 49 Python files