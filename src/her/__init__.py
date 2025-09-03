@@
     if name == "gateway_server":
         import importlib
         mod = importlib.import_module('.gateway_server', __name__)
         return mod
+    # Provide direct access to the high-level runtime orchestrator.
+    if name == "HerAgent":
+        try:
+            from .runtime.agent import HerAgent as _HA
+            return _HA
+        except Exception:
+            # If runtime dependencies (e.g. Playwright) are missing, return None
+            return None

@@
     __all__ = [
         "HybridClient",
         "HybridElementRetriever", 
         "HybridElementRetrieverClient",
         "HybridPipeline",
         "HERPipeline",
         "resolve_model_paths",
         "PipelineConfig",
         "ResilienceManager",
         "WaitStrategy",
         "InputValidator",
         "DOMValidator",
         "FormValidator",
         "AccessibilityValidator",
         "gateway_server",
+        "HerAgent",
         "__version__"
     ]
