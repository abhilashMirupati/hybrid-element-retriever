# Architecture Overview

This document provides a high‑level overview of the Hybrid Element Retriever (HER) framework.  The goal is to explain the responsibilities of each layer and how they interact to convert natural language steps into concrete user interface actions.

## Hybrid++ Pipeline

HER adopts a **Hybrid++** pipeline consisting of the following stages:

1. **Parser (Intent Extraction):** A lightweight component that extracts the action (e.g. click, type), target phrase and optional arguments from a plain English instruction.  The current implementation uses simple string manipulation; future versions could integrate a transformer‑based intent parser for better recall.

2. **Session Manager (Auto‑Index Brain):** Wraps a Playwright page instance and maintains a cache keyed by the origin, frame path and a DOM hash.  It listens for navigation events and triggers a fresh snapshot and index whenever a new page is loaded or the DOM changes significantly.  Tests and the UI never call `index()` directly; indexing is implicit.

3. **Element Inventory (DOM + AX Snapshot):** Retrieves the flattened DOM and the full accessibility tree via the Chrome DevTools Protocol (CDP) and joins them into a unified list of element descriptors.  Each descriptor contains tag information, accessibility roles/names, bounding boxes and other metadata.

4. **Retrieval (Semantic + Heuristic Fusion):** Embeds the query phrase and each element descriptor into dense vectors.  A late fusion combines semantic similarity with heuristic scores (e.g. role matches) to produce a ranked list of candidates.  The `rank.fusion` module contains a simple implementation.

5. **Locator Resolution (Semantic‑first):** Generates concrete locators (role‑based, CSS or XPath) from the top‑ranked candidates.  In this reference implementation the synthesiser returns the candidates unchanged.

6. **Execute + Verify:** Performs the requested action using Playwright.  A real implementation would scroll the element into view, guard against occlusion and verify that the state of the page changed as expected.  Here we simulate success.

7. **Self‑Heal + Promotion:** On failure the system retries with alternate locators, refreshes the DOM snapshot and promotes successful locators so they are ranked higher in the future.  The `recovery` package exposes placeholder functions.

## Embedding Cache

HER plans to use a two‑tier embedding cache:

* An in‑memory least recently used (LRU) cache for the most frequently used vectors.
* An on‑disk cache stored under `.cache/embeddings/` for persistence across sessions.

Both caches are keyed by a SHA‑1 hash of the element descriptor or normalised query along with the model ID and version.  A CLI flag `--clear-embed-cache` invalidates the caches.

## Configuration

All configurable parameters such as wait times, ranking weights and the DOM hash delta threshold are defined in `her.config`.  These values can be overridden when instantiating the `HybridClient` or by providing a configuration file.

## Limits of This Implementation

This repository intentionally omits production‑grade implementations of many components.  Notably:

* The CDP bridge does not talk to a real browser; snapshots return empty lists.
* Embeddings are generated using deterministic hash functions instead of neural models.
* The self‑healing and promotion subsystems are stubs.
* The Java wrapper is not implemented; only the Python API is available.

Despite these limitations the structure of the package follows best practices, including clear module boundaries, a test suite, documentation and continuous integration configuration.
