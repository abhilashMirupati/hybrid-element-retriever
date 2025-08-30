path | role | imports (top-level) | referenced_by_count | notes
---|---|---|---|---
ARCHIVE/root_tests/test_all_components.py | other | pathlib, sys, time | 0 | 
ARCHIVE/root_tests/test_all_fixes.py | other | her.cache.thread_safe_cache, her.embeddings.real_embedder, her.pipeline_final, pathlib, sys, threading, time | 0 | 
ARCHIVE/root_tests/test_complex_features.py | other | her.pipeline_production, json, pathlib, sys, time | 0 | 
ARCHIVE/root_tests/test_complex_html_xpath.py | other | her.locator.synthesize, her.pipeline, pathlib, sys | 0 | 
ARCHIVE/root_tests/test_debug_flow.py | other | her.pipeline, logging, pathlib, sys | 0 | 
ARCHIVE/root_tests/test_debug_phone.py | other | her.pipeline, pathlib, sys | 0 | 
ARCHIVE/root_tests/test_debug_phone2.py | other | pathlib, sys | 0 | 
ARCHIVE/root_tests/test_direct_score.py | other |  | 0 | 
ARCHIVE/root_tests/test_edge_cases_real.py | other | pathlib, sys | 0 | 
ARCHIVE/root_tests/test_final_component_analysis.py | other | her.actions, her.cache.two_tier, her.locator.synthesize, her.matching.intelligent_matcher, her.pipeline_v2, her.session.snapshot, pathlib, sys, time | 0 | 
ARCHIVE/root_tests/test_final_fix.py | other | her.pipeline, pathlib, sys | 0 | 
ARCHIVE/root_tests/test_final_nlp_verification.py | other | her.locator.synthesize, her.pipeline, pathlib, sys | 0 | 
ARCHIVE/root_tests/test_final_verification.py | other | sys | 0 | 
ARCHIVE/root_tests/test_fixes_work.py | other | her.locator.synthesize, her.parser.intent, her.pipeline_final, pathlib, sys | 0 | 
ARCHIVE/root_tests/test_her_comprehensive.py | other | dataclasses, json, os, shutil, time, typing, unittest.mock | 0 | 
ARCHIVE/root_tests/test_intelligent_matching.py | other | her.matching.intelligent_matcher, her.pipeline, her.pipeline_v2, pathlib, sys | 0 | 
ARCHIVE/root_tests/test_mock_scenarios.py | other | json, time, typing, unittest.mock | 0 | 
ARCHIVE/root_tests/test_nlp_improvements.py | other | her.pipeline, pathlib, sys | 0 | 
ARCHIVE/root_tests/test_phone_fresh.py | other | her.pipeline, pathlib, sys | 0 | 
ARCHIVE/root_tests/test_pipeline_debug.py | other | her.pipeline, sys | 0 | 
ARCHIVE/root_tests/test_pipeline_direct.py | other | her.pipeline, pathlib, sys | 0 | 
ARCHIVE/root_tests/test_real_integration.py | other | pathlib, sys | 0 | 
ARCHIVE/root_tests/test_reality_check.py | other | sys | 0 | 
ARCHIVE/root_tests/test_scoring_detail.py | other | pathlib, sys | 0 | 
ARCHIVE/root_tests/test_trace_phone.py | other |  | 0 | 
ARCHIVE/root_tests/test_trace_score.py | other |  | 0 | 
ARCHIVE/root_tests/test_uncached.py | other | subprocess, sys | 0 | 
ARCHIVE/src/cli_api_backup.py | cli | __future__, dataclasses, descriptors.merge, embeddings.element_embedder, embeddings.query_embedder, executor.actions, json, locator.enhanced_verify, locator.simple_synthesize, locator.verify… | 0 | 
ARCHIVE/src/cli_api_fixed.py | cli | __future__, dataclasses, descriptors.merge, embeddings.element_embedder, embeddings.query_embedder, locator.synthesize, locator.verify, logging, parser.intent, pathlib… | 0 | 
ARCHIVE/src/fusion_scorer_v2.py | other | dataclasses, difflib, math, re, typing | 0 | 
ARCHIVE/src/pipeline_final.py | other | cache.thread_safe_cache, dataclasses, embeddings.real_embedder, hashlib, locator.synthesize, locator.verify, logging, parser.intent, pipeline, scoring.fusion_scorer_v2… | 0 | 
ARCHIVE/src/pipeline_production.py | other | cache.two_tier, dataclasses, embeddings.element_embedder, embeddings.query_embedder, hashlib, locator.synthesize, locator.verify, logging, parser.intent, pipeline… | 0 | 
ARCHIVE/src/pipeline_v2.py | other | dataclasses, locator.synthesize, logging, matching.intelligent_matcher, pipeline, typing | 0 | 
ARCHIVE/src/sqlite_cache_old.py | other | __future__, pathlib, sqlite3, typing | 0 | sqlite
ARCHIVE/validation_scripts/brutal_self_critique.py | other |  | 0 | 
ARCHIVE/validation_scripts/brutal_self_critique_fixed.py | other | pathlib, sys, time, traceback | 0 | 
ARCHIVE/validation_scripts/example_usage.py | other | her.embeddings.element_embedder, her.embeddings.query_embedder, her.locator, her.parser.intent, her.rank.fusion | 0 | 
ARCHIVE/validation_scripts/final_brutal_critique.py | other | json, pathlib, random, sys, threading, time, traceback | 0 | 
ARCHIVE/validation_scripts/final_brutal_test.py | other | json, pathlib, sys, time | 0 | 
ARCHIVE/validation_scripts/fix_all_issues.py | other | pathlib, sys | 0 | 
ARCHIVE/validation_scripts/fix_failures.py | other | pathlib, sys | 0 | 
ARCHIVE/validation_scripts/run_final_validation.py | other | her.pipeline_production, pathlib, sys | 0 | 
ARCHIVE/validation_scripts/validate_integration.py | other | importlib, pathlib, sys | 0 | 
ARCHIVE/validation_scripts/validate_production.py | other | her.pipeline_production, her.scoring.fusion_scorer_v2, pathlib, sys, time | 0 | 
ARCHIVE/validation_scripts/verify_fixes.py | other | pathlib, sys | 0 | 
examples/advanced_features.py | other | her | 0 | 
examples/basic_usage.py | other | her | 0 | 
examples/complex_scenarios_demo.py | other | her.cli_api, logging | 0 | 
examples/demo.py | other | json, sys, typing | 0 | 
examples/edge_cases/test_runner.py | other | json, logging, pathlib, src.her.cli_api, src.her.locator.enhanced_verify, src.her.recovery.enhanced_promotion, src.her.session.enhanced_manager, sys, time, typing | 0 | 
her/scripts/run_functional_validation.py | other | asyncio, dataclasses, her.cli_api, json, logging, pathlib, playwright.async_api, rich.console, rich.progress, rich.table… | 0 | 
her/setup.py | other | os, setuptools | 0 | 
her/src/her/__init__.py | other | her.bridge.snapshot, her.cli_api, her.executor.session | 14 | dup-tree
her/src/her/bridge/snapshot.py | bridge | asyncio, dataclasses, hashlib, json, logging, playwright.async_api, typing | 13 | dup-tree
her/src/her/cli.py | cli | asyncio, click, her.cli_api, json, logging, pathlib, rich.console, rich.logging, rich.progress, rich.table… | 1 | dup-tree
her/src/her/cli_api.py | cli | asyncio, dataclasses, her.bridge.snapshot, her.embeddings.element_embedder, her.embeddings.query_embedder, her.executor.actions, her.executor.session, her.locator.synthesize, her.locator.verify, her.rank.fusion… | 24 | dup-tree
her/src/her/embeddings/_resolve.py | embeddings | json, logging, os, pathlib, typing | 6 | dup-tree
her/src/her/embeddings/element_embedder.py | embeddings | dataclasses, hashlib, her.bridge.snapshot, her.embeddings._resolve, logging, numpy, pathlib, typing | 14 | dup-tree
her/src/her/embeddings/query_embedder.py | embeddings | hashlib, her.embeddings._resolve, logging, numpy, pathlib, typing | 13 | dup-tree
her/src/her/executor/actions.py | executor | asyncio, dataclasses, enum, her.locator.verify, logging, playwright.async_api, time, typing | 6 | dup-tree
her/src/her/executor/session.py | executor | asyncio, dataclasses, hashlib, her.bridge.snapshot, json, logging, playwright.async_api, time, typing | 3 | dup-tree
her/src/her/locator/synthesize.py | locator | dataclasses, her.bridge.snapshot, logging, re, typing | 32 | dup-tree
her/src/her/locator/verify.py | locator | asyncio, dataclasses, logging, playwright.async_api, typing | 8 | dup-tree
her/src/her/rank/fusion.py | rank | collections, numpy, typing | 8 | dup-tree
her/src/her/recovery/promotion.py | recovery | aiosqlite, asyncio, dataclasses, json, logging, pathlib, time, typing | 5 | dup-tree sqlite
her/src/her/recovery/self_heal.py | recovery | dataclasses, her.bridge.snapshot, her.locator.synthesize, her.locator.verify, json, logging, time, typing | 5 | dup-tree
her/src/her/vectordb/sqlite_cache.py | vectordb | aiosqlite, asyncio, dataclasses, hashlib, json, logging, numpy, pathlib, time, typing | 6 | dup-tree sqlite
her/test_basic.py | other | asyncio, her, pathlib, sys | 0 | 
her/test_imports.py | other | pathlib, sys | 0 | 
samples/site/server.py | other | http.server, os, socketserver | 0 | 
scripts/run_functional_validation.py | other | asyncio, dataclasses, her.pipeline, http.server, json, os, pathlib, playwright.async_api, sys, threading… | 0 | 
setup.py | other | pathlib, setuptools | 2 | 
src/her/__init__.py | other |  | 14 | canonical
src/her/actions.py | other | dataclasses, enum, logging, time, typing | 18 | canonical
src/her/bridge/__init__.py | bridge | cdp_bridge, snapshot | 1 | canonical
src/her/bridge/cdp_bridge.py | bridge | dataclasses, hashlib, json, logging, typing | 5 | canonical
src/her/bridge/snapshot.py | bridge | __future__, cdp_bridge, hashlib, logging, typing | 13 | canonical
src/her/cache/__init__.py | other | two_tier | 0 | canonical
src/her/cache/thread_safe_cache.py | other | collections, json, pathlib, threading, time, typing | 3 | canonical
src/her/cache/two_tier.py | other | collections, config, dataclasses, hashlib, json, logging, pathlib, pickle, sqlite3, threading… | 15 | canonical sqlite
src/her/cli.py | cli | __future__, cli_api, dataclasses, json, sys, typing | 1 | canonical
src/her/cli_api.py | cli | __future__, dataclasses, descriptors.merge, embeddings.element_embedder, embeddings.query_embedder, executor.actions, locator.synthesize, locator.verify, logging, parser.intent… | 24 | canonical
src/her/config.py | other | os, pathlib | 2 | canonical
src/her/descriptors/__init__.py | other | dataclasses, merge, typing | 2 | canonical
src/her/descriptors/merge.py | other | logging, typing | 0 | canonical
src/her/descriptors.py | other | dataclasses, typing | 2 | canonical
src/her/embeddings/__init__.py | embeddings | _resolve, element_embedder, query_embedder | 1 | canonical
src/her/embeddings/_resolve.py | embeddings | __future__, dataclasses, json, os, pathlib, typing | 6 | canonical
src/her/embeddings/cache.py | embeddings | hashlib, pathlib, pickle, typing | 3 | canonical
src/her/embeddings/element_embedder.py | embeddings | hashlib, json, numpy, onnxruntime, os, pathlib, typing | 14 | canonical
src/her/embeddings/enhanced_element_embedder.py | embeddings | element_embedder, hashlib, logging, typing, vectordb.sqlite_cache | 0 | canonical
src/her/embeddings/fallback_embedder.py | embeddings | hashlib, math, typing | 1 | canonical
src/her/embeddings/minilm_embedder.py | embeddings | hashlib, json, numpy, pathlib, typing | 0 | canonical
src/her/embeddings/query_embedder.py | embeddings | __future__, _resolve, hashlib, numpy, typing | 13 | canonical
src/her/embeddings/real_embedder.py | embeddings | hashlib, json, logging, typing | 3 | canonical
src/her/embeddings/text_embedder.py | embeddings | __future__, hashlib, json, numpy, onnxruntime, pathlib, transformers, typing | 0 | canonical
src/her/executor/__init__.py | executor |  | 1 | canonical
src/her/executor/actions.py | executor | __future__, dataclasses, logging, time, typing | 6 | canonical
src/her/executor/session.py | executor | __future__, dataclasses, hashlib, numpy, pathlib, time, typing, vectordb.two_tier_cache | 3 | canonical
src/her/gateway_server.py | other | cli_api, logging, sys | 6 | canonical
src/her/handlers/__init__.py | other |  | 0 | canonical
src/her/handlers/complex_scenarios.py | other | dataclasses, logging, time, typing | 2 | canonical
src/her/locator/__init__.py | locator |  | 2 | canonical
src/her/locator/enhanced_verify.py | locator | dataclasses, logging, synthesize, time, typing, vectordb.sqlite_cache, verify | 5 | canonical
src/her/locator/simple_synthesize.py | locator | synthesize, typing | 0 | canonical
src/her/locator/synthesize.py | locator | __future__, logging, typing | 32 | canonical
src/her/locator/verify.py | locator | __future__, dataclasses, typing | 8 | canonical
src/her/matching/intelligent_matcher.py | other | dataclasses, difflib, math, re, typing | 5 | canonical
src/her/mock_client.py | cli | hashlib, json, pathlib, time, typing | 2 | canonical
src/her/models/__init__.py | other |  | 0 | canonical
src/her/parser/__init__.py | other |  | 1 | canonical
src/her/parser/intent.py | other | dataclasses, logging, re, typing | 10 | canonical
src/her/pipeline.py | other | her.embedders.element_embedder, her.embedders.text_embedder, her.rank.fusion, her.utils.cache, time, typing | 55 | canonical
src/her/production_client.py | cli | cache.two_tier, json, pathlib, rank.semantic_fusion, time, typing | 1 | canonical
src/her/rank/__init__.py | rank | fusion_scorer | 1 | canonical
src/her/rank/fusion.py | rank | __future__, dataclasses, typing | 8 | canonical
src/her/rank/fusion_scorer.py | rank | config, math, typing | 8 | canonical
src/her/rank/heuristics.py | rank | __future__, typing | 3 | canonical
src/her/rank/semantic_fusion.py | rank | embeddings.minilm_embedder, numpy, pathlib, typing | 0 | canonical
src/her/recovery/__init__.py | recovery |  | 1 | canonical
src/her/recovery/enhanced_promotion.py | recovery | __future__, dataclasses, datetime, json, logging, pathlib, sqlite3, typing | 0 | canonical sqlite
src/her/recovery/enhanced_self_heal.py | recovery | bridge.cdp_bridge, cache.two_tier, dataclasses, enum, locator.synthesize, logging, pathlib, re, time, typing | 1 | canonical
src/her/recovery/promotion.py | recovery | __future__, dataclasses, json, pathlib, sqlite3, time, typing | 5 | canonical sqlite
src/her/recovery/self_heal.py | recovery | __future__, dataclasses, locator.verify, promotion, typing | 5 | canonical
src/her/resilience.py | other | dataclasses, enum, logging, time, typing | 11 | canonical
src/her/session/__init__.py | other |  | 1 | canonical
src/her/session/enhanced_manager.py | other | bridge.snapshot, dataclasses, datetime, hashlib, json, logging, pathlib, pickle, typing, utils.cache… | 3 | canonical
src/her/session/manager.py | other | bridge.snapshot, dataclasses, datetime, embeddings.element_embedder, json, logging, pathlib, typing, vectordb.faiss_store | 15 | canonical
src/her/session/snapshot.py | other | dataclasses, hashlib, logging, time, typing | 10 | canonical
src/her/utils/__init__.py | other | hashlib, re, typing | 6 | canonical
src/her/utils/cache.py | other | collections, hashlib, json, os, pickle, threading, typing | 1 | canonical
src/her/utils/config.py | other | __future__, dataclasses | 0 | canonical
src/her/utils.py | other | hashlib, typing | 6 | canonical
src/her/validators.py | other | logging, re, typing, unicodedata, urllib.parse | 11 | canonical
src/her/vectordb/__init__.py | vectordb |  | 1 | canonical
src/her/vectordb/faiss_store.py | vectordb | math, typing | 5 | canonical
src/her/vectordb/sqlite_cache.py | vectordb | dataclasses, json, logging, pathlib, pickle, sqlite3, threading, time, typing | 6 | canonical sqlite
src/her/vectordb/two_tier_cache.py | vectordb | __future__, collections, json, numpy, os, pathlib, sqlite3, struct, threading, time… | 1 | canonical sqlite
tests/conftest.py | tests | os, pathlib, pytest, sys | 0 | 
tests/core/test_cache_resolver.py | tests | her.embeddings._resolve, her.vectordb.two_tier_cache, json, pathlib | 0 | 
tests/core/test_cold_start.py | tests | her.cache.two_tier, her.embeddings.element_embedder, her.pipeline, json, pathlib, pytest, unittest.mock | 0 | 
tests/core/test_incremental_update.py | tests | her.cache.two_tier, her.pipeline, pytest, unittest.mock | 0 | 
tests/dom/test_frames_shadow.py | tests | her.pipeline, pytest, unittest.mock | 0 | 
tests/final/test_cli_contract.py | tests | json, subprocess | 0 | 
tests/perf/test_cache_hit_latency.py | tests | her.cache.two_tier, her.pipeline, pytest, statistics, time | 0 | 
tests/perf/test_large_dom_stress.py | tests | her.pipeline, pytest, time | 0 | 
tests/resilience/test_waits_overlays.py | tests | her.pipeline, her.resilience, pytest, time, unittest.mock | 0 | 
tests/retrieval/test_embedders.py | tests | her.embeddings.element_embedder, her.embeddings.query_embedder, numpy | 0 | 
tests/retrieval/test_nlp_scoring.py | tests | her.pipeline, her.rank.fusion, pytest | 0 | 
tests/retrieval/test_strategy_fallbacks.py | tests | her.pipeline, pytest, unittest.mock | 0 | 
tests/spa/test_spa_route_listeners.py | tests | her.pipeline, pytest, unittest.mock | 0 | 
tests/test_all_components.py | tests | pathlib, sys, time | 0 | 
tests/test_all_fixes.py | tests | her.cache.thread_safe_cache, her.embeddings.real_embedder, her.pipeline, pathlib, sys, threading, time | 0 | 
tests/test_basic.py | tests | os, sys | 0 | 
tests/test_bridge.py | tests | her.bridge.cdp_bridge, her.bridge.snapshot, json, pytest, unittest.mock | 0 | 
tests/test_bridge_mapping.py | tests | her.bridge.snapshot | 0 | 
tests/test_cli_api.py | tests | her.cli_api, json, numpy, pytest, unittest.mock | 0 | 
tests/test_cli_coverage.py | tests | her.cli, io, json, pytest, sys, unittest.mock | 0 | 
tests/test_complex_features.py | tests | her.pipeline, json, pathlib, sys, time | 0 | 
tests/test_complex_html_xpath.py | tests | her.locator.synthesize, her.pipeline, pathlib, sys | 0 | 
tests/test_complex_scenarios.py | tests | her.handlers.complex_scenarios, pytest, time, unittest.mock | 0 | 
tests/test_comprehensive_validation.py | tests | her.cache.two_tier, her.pipeline, her.rank.fusion_scorer, pathlib, pytest, time | 0 | 
tests/test_corpus_complex.py | tests | her.embeddings.element_embedder, her.embeddings.query_embedder | 0 | 
tests/test_coverage_boost.py | tests | json, numpy, pathlib, pytest, unittest.mock | 0 | 
tests/test_debug_flow.py | tests | her.pipeline, logging, pathlib, sys | 0 | 
tests/test_debug_phone.py | tests | her.pipeline, pathlib, sys | 0 | 
tests/test_debug_phone2.py | tests | pathlib, sys | 0 | 
tests/test_descriptors.py | tests | her.descriptors | 0 | 
tests/test_direct_score.py | tests |  | 0 | 
tests/test_dom_uniqueness.py | tests | her.locator.enhanced_verify, her.locator.synthesize, her.session.snapshot, pathlib, pytest, sys, unittest.mock | 0 | 
tests/test_e2e_demo.py | tests | her.cli_api | 0 | 
tests/test_edge_cases.py | tests | her.pipeline, her.resilience, her.validators, json, pathlib, pytest, sys, unittest.mock | 0 | 
tests/test_edge_cases_real.py | tests | pathlib, sys | 0 | 
tests/test_embeddings.py | tests | her.embeddings._resolve, her.embeddings.cache, her.embeddings.element_embedder, her.embeddings.query_embedder, numpy, pathlib, pytest, tempfile | 0 | 
tests/test_examples.py | tests | her.bridge.snapshot, her.cli_api, her.executor.actions, her.locator.verify, json, pathlib, pytest, time, typing | 0 | 
tests/test_executor_coverage.py | tests | her.executor.actions, pytest, unittest.mock | 0 | 
tests/test_final_component_analysis.py | tests | her.actions, her.cache.two_tier, her.locator.synthesize, her.matching.intelligent_matcher, her.pipeline, her.session.snapshot, pathlib, sys, time | 0 | 
tests/test_final_fix.py | tests | her.pipeline, pathlib, sys | 0 | 
tests/test_final_nlp_verification.py | tests | her.locator.synthesize, her.pipeline, pathlib, sys | 0 | 
tests/test_final_verification.py | tests | sys | 0 | 
tests/test_fixes_work.py | tests | her.locator.synthesize, her.parser.intent, her.pipeline, pathlib, sys | 0 | 
tests/test_frames_shadow.py | tests | her.actions, her.locator.enhanced_verify, her.session.snapshot, pathlib, pytest, sys, unittest.mock | 0 | 
tests/test_full_coverage.py | tests | her.bridge.cdp_bridge, her.bridge.snapshot, her.cache.two_tier, her.cli_api, her.descriptors, her.embeddings.cache, her.embeddings.element_embedder, her.embeddings.fallback_embedder, her.embeddings.query_embedder, her.executor.actions… | 0 | 
tests/test_gateway.py | tests | pytest, sys, unittest.mock | 0 | 
tests/test_her_comprehensive.py | tests | dataclasses, json, os, shutil, time, typing, unittest.mock | 0 | 
tests/test_integration.py | tests | her, her.cli_api, her.session.enhanced_manager, her.session.manager, pathlib, pytest, sys, time, unittest.mock | 0 | 
tests/test_intelligent_matching.py | tests | her.matching.intelligent_matcher, her.pipeline, pathlib, sys | 0 | 
tests/test_json_contract.py | tests | her.actions, her.locator.enhanced_verify, json, pathlib, pytest, sys | 0 | 
tests/test_loading_overlays.py | tests | her.actions, pathlib, pytest, sys, unittest.mock | 0 | 
tests/test_locator.py | tests | her.locator.synthesize, her.locator.verify, pytest, unittest.mock | 0 | 
tests/test_mock_scenarios.py | tests | json, time, typing, unittest.mock | 0 | 
tests/test_network_idle.py | tests | her.actions, pathlib, pytest, sys, time, unittest.mock | 0 | 
tests/test_nlp_improvements.py | tests | her.pipeline, pathlib, sys | 0 | 
tests/test_nlp_scoring.py | tests | her.pipeline, her.rank.fusion_scorer, pathlib, sys, typing, unittest | 0 | 
tests/test_overlays_and_visibility.py | tests |  | 0 | 
tests/test_parser.py | tests | her.parser.intent, pytest | 0 | 
tests/test_performance.py | tests | her.cache.two_tier, her.embeddings.element_embedder, her.embeddings.query_embedder, her.locator.synthesize, her.pipeline, pathlib, pytest, random, sys, time… | 0 | 
tests/test_phone_fresh.py | tests | her.pipeline, pathlib, sys | 0 | 
tests/test_pipeline_debug.py | tests | her.pipeline, sys | 0 | 
tests/test_pipeline_direct.py | tests | her.pipeline, pathlib, sys | 0 | 
tests/test_pipeline_full.py | tests | her.pipeline, pathlib, sys, time, typing, unittest | 0 | 
tests/test_rank.py | tests | her.rank.fusion, her.rank.heuristics, json, pathlib, pytest, tempfile, unittest.mock | 0 | 
tests/test_rank_and_locator.py | tests | her.rank.fusion | 0 | 
tests/test_real_integration.py | tests | pathlib, sys | 0 | 
tests/test_reality_check.py | tests | sys | 0 | 
tests/test_realworld_examples.py | tests | her.bridge.cdp_bridge, her.cache.two_tier, her.cli_api, her.rank.fusion_scorer, her.recovery.enhanced_self_heal, json, os, pathlib, pytest, sys… | 0 | 
tests/test_recovery.py | tests | datetime, her.recovery.promotion, her.recovery.self_heal, json, pathlib, pytest, tempfile, unittest.mock | 0 | 
tests/test_resolver_coverage.py | tests | her.embeddings._resolve, numpy, pytest, unittest.mock | 0 | 
tests/test_scoring_detail.py | tests | pathlib, sys | 0 | 
tests/test_self_heal_and_promotion.py | tests | her.recovery.promotion, her.recovery.self_heal | 0 | 
tests/test_session.py | tests | datetime, her.session.manager, pytest, time, unittest.mock | 0 | 
tests/test_session_auto_index.py | tests | her.session.manager | 0 | 
tests/test_session_coverage.py | tests | datetime, her.session.manager, pytest, unittest.mock | 0 | 
tests/test_simple_coverage.py | tests | numpy, pytest, unittest.mock | 0 | 
tests/test_smoke.py | tests |  | 0 | 
tests/test_spa_route_listeners.py | tests | her.session.snapshot, pathlib, pytest, sys, unittest.mock | 0 | 
tests/test_trace_phone.py | tests |  | 0 | 
tests/test_trace_score.py | tests |  | 0 | 
tests/test_uncached.py | tests | subprocess, sys | 0 | 
tests/test_utils_coverage.py | tests | her.utils, pytest | 0 | 
tests/test_waits_and_timeouts.py | tests | her.config | 0 | 
tests/test_zero_index_flow.py | tests | her.cli_api, pytest | 0 | 