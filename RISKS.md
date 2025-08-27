# Risks & Mitigations

The following table outlines the primary risks associated with bringing the Hybrid Element Retriever (HER) to a production‑ready state and suggests mitigation strategies for each.

| Risk | Impact | Mitigation |
| --- | --- | --- |
| **ONNX model availability** | Pre‑trained MiniLM/E5‑small and MarkupLM‑base models may be unavailable or large, causing installation delays or licensing concerns. | Download the models once during the build phase and cache them in the repository or via a model registry.  Use quantised versions (INT8) to reduce size.  Document the download process in the setup scripts. |
| **Playwright install failures on Windows** | Installing the Chromium browsers may fail on Windows due to antivirus restrictions or missing dependencies. | Provide `dev_setup.ps1` and `dev_setup.sh` scripts that call `playwright install chromium`.  Include troubleshooting steps in the README and detect platform‑specific issues. |
| **Headless browser instability in CI** | CI environments sometimes encounter crashes or GPU issues when running headless browsers. | Use the official Playwright GitHub Action or install `playwright` with `--with-deps` to ensure all dependencies are present.  Run tests using the `--browser=chromium` flag and retry on failures. |
| **SQLite and file permissions** | The embedding cache and promotion store rely on file system access; read/write permissions might be restricted in some environments. | Store cache files in a configurable directory (default to `.cache/`).  Provide CLI options to override the cache path.  Handle exceptions gracefully and fallback to in‑memory mode if on‑disk storage is unavailable. |
| **Performance bottlenecks** | ONNX inference and CDP snapshots could introduce latency, especially on CPU‑bound machines. | Benchmark the snapshot, embedding and retrieval phases; tune batch sizes and use quantised models.  Implement asynchronous snapshotting to overlap I/O and computation. |
| **Complexity of auto‑indexing** | Implementing correct SPA route detection, delta indexing and cache invalidation is error‑prone. | Add comprehensive unit and integration tests for navigation events, dom_hash calculation and cache eviction.  Instrument code to log indexing decisions and make thresholds configurable. |
| **Cross‑language integration via Py4J** | The Java wrapper introduces an additional layer of complexity and potential failure points. | Keep the Java API thin and delegate all heavy logic to Python.  Write end‑to‑end smoke tests that run the Java client against the Python server as part of CI. |
| **Security considerations** | Executing arbitrary pages could expose the tool to malicious HTML, XSS or drive‑by downloads. | Run the browser in a sandboxed environment with restricted permissions.  Disallow external network access by default and document the security model.  Provide guidelines for safe usage. |

