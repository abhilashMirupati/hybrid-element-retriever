# Hybrid Element Retriever

Hybrid Element Retriever (HER) is a proof‑of‑concept framework for turning plain English test steps into concrete UI actions.  The primary goal of HER is to demonstrate how a hybrid approach – combining semantic retrieval, rule‑based parsing and Playwright automation – can be used to interact with modern web applications without brittle, hand‑written locators.

**Important:** this repository is a reference implementation and does **not** contain a fully featured automation platform.  It showcases the high level structure required to build one, including automatic DOM indexing, semantic element retrieval and self‑healing.  Contributors are encouraged to extend the provided stubs and plug in their own models, databases and heuristics.

## Features

* **Automatic indexing:** the framework automatically snapshots and indexes the DOM and accessibility tree as you navigate, without ever requiring the tester to manually call an index API.  Indexing is triggered on first use, when the URL or frame changes, when the DOM has changed beyond a threshold or when a locator fails.
* **Natural language parsing:** a lightweight parser extracts intent from plain English test steps.  The parser outputs an action, target phrase and optional arguments or constraints.
* **Hybrid retrieval:** the system uses a semantic embedder to find the most relevant element descriptions.  A fusion of semantic scores and heuristic signals (e.g. roles, names and attributes) produces a ranked list of locator candidates.
* **Self healing:** when a locator fails the system falls back to alternate strategies, performs a fresh snapshot and promotes successful locators so they are preferred on subsequent runs.
* **Cross‑language:** a thin Java wrapper is provided via `py4j` so that Java tests can consume the same API.  A Maven template is included under `ci/` for reference.

## Quickstart

### Installation

Install the package from source.  This project requires Python 3.9 or higher.

```bash
git clone https://example.com/hybrid_element_retriever.git
cd hybrid_element_retriever
pip install .[dev]
```

After installation you must install the browser binaries used by
Playwright **and** download the ONNX models used by HER.  Run the
following commands from the repository root:

```bash
# Install Playwright browsers (Chromium is required)
python -m playwright install chromium

# Download and export ONNX models (MiniLM/E5‑small and MarkupLM‑base)
./scripts/install_models.sh
```

On Windows use the PowerShell script instead:

```powershell
python -m playwright install chromium
./scripts/install_models.ps1
```

The model installation scripts download the pretrained models from
Hugging Face and export them to ONNX format.  The exported files are
stored under ``src/her/models`` and will be picked up automatically at
runtime.  If the models are not present HER will fall back to a
deterministic hash‑based embedding scheme.

### CLI usage

HER exposes a simple CLI that can be used without writing code.  The CLI will automatically index pages and perform actions for you.

```bash
python -m her.cli act --url https://example.com/login --step "Click the login button"

python -m her.cli query "Email input" --url https://example.com/login
```

Both commands will produce JSON output describing how the framework interpreted your request, the locators it chose and any self‑healing attempts.

### API usage

You can also import the Python client directly in your tests.  **Do not call `index()` directly** – the framework handles indexing automatically.

```python
from her.cli_api import HybridClient

# create a client; auto_index is enabled by default
client = HybridClient()

# perform an action on a page
result = client.act("Click the submit button", url="https://example.com/form")
print(result)

# query elements without performing an action
candidates = client.query("Search field", url="https://example.com")
for cand in candidates:
    print(cand.selector, cand.score)
```

### Contributing

The current implementation provides many extension points.  If you wish to improve the element embeddings, plug in a faster vector database or extend the Java wrapper, consult the architecture document under `docs/ARCHITECTURE.md` and the TODO list in `TODO_LIST.md`.

Please run the provided checks before submitting a pull request:

```bash
./scripts/verify_project.sh
```

This script runs formatting, static type checks and unit tests.  All tests should pass (coverage ≥ 80%).

## License

This project is licensed under the MIT License.  See the `LICENSE` file for details.
