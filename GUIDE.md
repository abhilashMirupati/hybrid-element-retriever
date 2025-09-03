Hybrid Element Retriever (HER) – Detailed Guide

This guide explains how to set up, understand, and use the Hybrid Element Retriever framework, even if you have little prior experience. It covers installation, project structure, code flow, usage patterns (including handling edge cases such as cold/warm starts and frames), and identifies files that are primarily documentation or examples and may be removed from a production deployment.

1. Installation

Ensure Python 3.10+ is available. HER relies on modern Python features and ONNX runtimes.

Create and activate a virtual environment (recommended to avoid polluting your system). On Linux/macOS:

python3 -m venv .venv
source .venv/bin/activate


On Windows (PowerShell):

py -m venv .venv
.venv\Scripts\Activate.ps1


Install the package and dependencies. In the root of the project run:

pip install -e ".[playwright]"


The [playwright] extra installs Playwright support; omit it if you will integrate a different browser automation tool.

For development or testing, you can install all extras using pip install -e ".[dev]" or pip install -e ".[all]".

Install Playwright’s browser (one‑time):

python -m playwright install chromium


Download the ONNX models (if not already present). Run the helper script:

./scripts/install_models.sh


This populates src/her/models/ with e5-small-onnx and markuplm-base-onnx. When offline or during continuous integration, the installer creates stub files so the system still functions.

Verify sources compile (optional):

python -m compileall src


After these steps, the package is ready for use.

2. Repository Structure

The key runtime code lives in src/her. Below is a high‑level overview of the most important components:

Module/Directory	Purpose
pipeline.py	Implements the HybridPipeline. It orchestrates query embedding (using QueryEmbedder), element embedding (using ElementEmbedder), computes semantic & heuristic scores, and returns the best candidate. This is the core of the retrieval system.
compat.py	Provides the HERPipeline wrapper for backwards compatibility and includes functions to capture DOM snapshots, embed queries/elements, rerank candidates, detect cold starts, handle route changes, detect frame changes, and check element occlusion. It uses bridge/snapshot.py to capture the DOM and accessibility tree and gracefully degrades when Playwright is unavailable.
actions.py	Defines UI automation actions (click, type, scroll). Uses Playwright if available; otherwise returns default responses.
bridge/	Contains utilities for interacting with the browser via Chrome DevTools. cdp_bridge.py provides low‑level functions to retrieve flattened DOM and accessibility nodes; snapshot.py merges them into descriptors and computes stable DOM hashes. These functions are critical for capturing the page state.
cache/	Implements two‑tier caching (TwoTierCache) for storing embeddings and query results. Caching enables warm‑start behaviour: once a DOM is indexed, subsequent queries reuse cached embeddings for speed.
embeddings/	Houses embedders for queries and elements. query_embedder.py loads an E5 model to embed natural‑language queries; element_embedder.py wraps MarkupLM to embed HTML elements. Fallback embedders exist for offline scenarios.
rank/	Contains scoring logic. fusion_scorer.py merges semantic scores, CSS heuristics (boosts buttons/links and text matches), and promotion scores (from self‑healing) to produce a ranked list.
locator/	Responsible for synthesizing selectors and verifying their uniqueness. verify.py provides verify_selector and the backward‑compatible verify_locator (added for legacy tests) that determine whether a selector uniquely identifies an element, both online and offline. enhanced_verify.py adds frame awareness and self‑healing.
recovery/	Implements self‑healing strategies. self_heal.py generates alternative selectors when the primary selector fails and records promotion statistics.
resilience.py	Provides higher‑level helpers to wait for the page to be idle, detect and dismiss overlays, and handle infinite scrolling. These tools help automate dynamic pages.
utils/ & validators.py	Offer input validation (e.g., sanitizing queries and XPaths) and miscellaneous helper functions.
gateway_server.py & production_client.py	Set up a server and a client that allow remote RPC calls into the pipeline; useful for deploying HER as a microservice.

Several other files support examples, testing, or Java integration (e.g., the java directory). They are not required to run the Python pipeline.

3. How the Code Flows

Capture the DOM: Use bridge.snapshot.capture_snapshot(page) or any DOM instrumentation you prefer to obtain a list of element descriptors and a DOM hash. In the CLI (her query), this is done automatically.

Cold Start vs Warm Start:

On the first call to the pipeline (cold start), there are no cached embeddings. The pipeline computes query and element embeddings from scratch and stores them. This can take ~500 ms for moderate pages.

On subsequent calls with the same DOM hash (warm start), embeddings are loaded from the cache, so only the new query embedding needs to be computed. Warm queries typically complete in <2 seconds even on large DOMs.

Embed the Query: QueryEmbedder.batch_encode([query]) produces a fixed‑length vector for the natural language query. The E5 model captures semantic intent (e.g., synonyms like “submit” and “send”).

Embed DOM Elements: Each element descriptor is hashed to check if an embedding exists in the cache. If not, ElementEmbedder.batch_encode encodes the element using MarkupLM; otherwise, the cached embedding is reused.

Score Elements: For each candidate element, the pipeline computes:

Semantic score: cosine similarity between the query vector and element vector.

CSS/text heuristics: a small boost for elements with interactive tags (button, a, input, etc.) and for elements whose inner text contains words from the query.

Promotions: optional bonus scores from the self‑healing module.

Fusion & Ranking: FusionScorer.score_elements merges the above scores and sorts elements in descending order. The top candidate becomes the returned element; the pipeline also emits metadata (confidence, strategy used, frame information, shadow‑DOM flags).

Return Results: HybridPipeline.query returns a dictionary containing the best element (or None), its XPath, confidence score, and metadata. The HERPipeline.process wrapper adds fast‑path scanning for huge DOMs and normalizes metadata for legacy tests.

Handling Edge Cases

Large DOMs: When the snapshot contains thousands of elements, HERPipeline uses a fast path (_text_fast_path) that scans element text for the query words and returns a candidate quickly. This avoids embedding thousands of elements.

Frames & IFrames: Descriptors include a frame_path list. The returned result has frame_path and used_frame_id. Use locator.enhanced_verify to verify selectors within specific frames. The compat._detect_frame_change function compares frame IDs to reset caches when navigation occurs.

Shadow DOM: Elements inside shadow roots are marked with in_shadow_dom; the pipeline handles them like normal elements. If you interact via Playwright, you need to pierce shadow roots using page.locator() or querySelector() with the appropriate options.

SPA Navigation: Single‑page applications modify the DOM without full reloads. The compat._add_browser_listener method attaches a framenavigated event to Playwright’s page; when triggered, _on_route_change clears caches so the next call re‑indexes the new DOM.

Cold vs Warm: Use compat._is_cold_start() or check whether self._last_dom_hash is None to determine if the pipeline is in a cold state. In warm state, incremental updates may only embed new/changed elements (enabled in PipelineConfig).

Occlusion & Visibility: compat._is_element_occluded samples the center of the element’s bounding box using document.elementFromPoint; if a different element is returned, the candidate is likely occluded. This can help you avoid clicking hidden elements.

4. Using HER in Your Project

Below are typical ways to leverage HER. You can use either the high‑level CLI, the Python API, or embed it into a larger automation framework.

4.1 CLI Usage
# Check version
her version

# Query a live site (requires Playwright)
her query "Find the submit button" --url https://example.com

# Save a snapshot and query offline
her snapshot --url https://example.com --out snapshot.json
her query "Find 'Sign Up'" --snapshot snapshot.json


The CLI automatically captures the DOM, runs the pipeline, and prints the best XPath along with metadata.

4.2 Python API
from her.pipeline import HybridPipeline
from her.bridge.snapshot import capture_snapshot

# 1. Capture descriptors from a Playwright page
page = ...  # obtained from playwright.sync_api
descriptors, dom_hash = capture_snapshot(page)

# 2. Run the pipeline
pipeline = HybridPipeline()
result = pipeline.query("Find the submit button", descriptors)

# 3. Use the result
if result["xpath"]:
    print("Best XPath:", result["xpath"])
    # Optionally click it via Playwright
    element = page.query_selector(f"xpath={result['xpath']}")
    if element:
        element.click()


You can also instantiate HERPipeline(config) when you need the legacy fast path or additional helpers exposed in the compatibility layer.

4.3 Integrating Resilience Features
from her.resilience import ResilienceManager, WaitStrategy

resilience = ResilienceManager()

# Wait for the page to be idle (network and DOM stable)
resilience.wait_for_idle(page, WaitStrategy.NETWORK_IDLE)

# Handle infinite scrolling pages
resilience.handle_infinite_scroll(page, max_scrolls=5)

# Dismiss overlays/pop‑ups automatically
resilience.detect_and_handle_overlay(page)


These utilities help ensure the page is in a good state before you capture the DOM and query elements.

4.4 Self‑Healing & Recovery

If a selector breaks (e.g., the page changes), you can use the recovery module:

from her.recovery.self_heal import SelfHealer
from her.locator.verify import verify_locator

healer = SelfHealer()

# Suppose your primary XPath no longer works
primary_xpath = "//button[@id='submit']"

# Use verify_locator to check
vr = verify_locator(page, primary_xpath, strategy="xpath", require_unique=True)

if not vr.ok:
    # Generate fallback selectors
    candidates = healer.heal(primary_xpath, page)
    for sel, strategy_name in candidates:
        print(f"Trying {strategy_name}: {sel}")
        # you can verify and click using Playwright


Self‑healing tries various transformations (e.g., relaxing exact text match, removing indices, converting IDs to contains(@id, ...), etc.) and records successful promotions in a SQLite cache.

5. Files and Documentation You Can Remove

For a production deployment, many files in this repository are only needed for development or documentation. The following can be safely omitted without affecting runtime functionality:

.md documentation files: CHANGELOG.md, COMPONENTS_MATRIX.md, CONTRIBUTING.md, PERF_REPORT.md, RELEASE_GATE.md, RISKS.md, SCORING_NOTES.md, and the files under archive/. They provide background information, performance reports and critique notes.

Development docs: Everything under docs/ (ARCHITECTURE.md, COMPLEX_SCENARIOS_GUIDE.md, DIAGRAMS.md) and the examples/ directory. These are tutorials and demonstration scripts.

Testing harness: The functional_harness/, samples/, and tests/ directories contain test fixtures and harness code. Remove them if you are not running the test suite in production.

CI configuration: The ci/ folder (GitHub Actions workflow) and requirements-dev.txt are only used for continuous integration.

Virtual environment: The venv/ folder that may come bundled in the repository is not needed if you create your own virtual environment.

Java wrapper: The java/ directory contains a Java client built with Py4J. Remove this if you do not need JVM integration.

Scripts used for development: Files in scripts/ (e.g., doctor.py, profile_runs.py, run_functional_validation.py) are helpful during development but not required at runtime.

Removing these files reduces the footprint of your deployment and simplifies maintenance. Keep only the src/her package, the ONNX models in src/her/models/, and the CLI entrypoints (her defined in setup.py) for a minimal production build.

6. Final Notes

Dependency Management: HER relies on Playwright for browser automation and on ONNX for machine‑learning models. Ensure these dependencies are installed in your environment. If offline, the framework falls back to deterministic hashing so that it still functions, though semantic accuracy is reduced.

Cold/Warm Start Awareness: The first call will take longer because embeddings must be generated. Subsequent queries with the same DOM are much faster thanks to caching. Clear the cache when the page navigates or the DOM changes significantly (handled automatically by HERPipeline._on_route_change if you attach browser listeners).

Extensibility: The modular structure (embedders, rankers, resilience, recovery) allows you to plug in your own models or heuristics if needed. For example, you can implement a custom FusionScorer to prioritise particular element types or modify the embedding size by providing a different ONNX model.

By following the installation steps and referring to the descriptions above, even someone without a background in natural‑language processing or UI automation can set up and start using the Hybrid Element Retriever. The framework hides complex details behind simple APIs while offering hooks to handle advanced scenarios like single‑page applications, shadow DOMs, cold starts and self‑healing.
