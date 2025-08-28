package com.hybridclient.her;

import py4j.GatewayServer;
import py4j.Py4JException;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.ArrayList;
import java.util.logging.Logger;
import java.util.logging.Level;

/**
 * Production-ready Java wrapper for the Python Hybrid Element Retriever.
 *
 * <p>This class uses Py4J to connect to a running Python gateway server that
 * exposes the HybridClient API. The Python side must start a GatewayServer
 * and register the client as the entry point.</p>
 * 
 * <p>Example usage:</p>
 * <pre>{@code
 * HybridClientJ client = new HybridClientJ();
 * try {
 *     Map<String, Object> result = client.act("Click login button", "https://example.com");
 *     if ((Boolean) result.get("success")) {
 *         System.out.println("Action successful!");
 *     }
 * } finally {
 *     client.shutdown();
 * }
 * }</pre>
 */
public class HybridClientJ {
    private static final Logger LOGGER = Logger.getLogger(HybridClientJ.class.getName());
    private static final int DEFAULT_PORT = 25333;
    private static final int CONNECTION_TIMEOUT_MS = 10000;
    
    private final GatewayServer gateway;
    private final Object pythonClient;
    private volatile boolean isConnected = false;

    /**
     * Create a new HybridClientJ with default settings.
     */
    public HybridClientJ() {
        this(DEFAULT_PORT);
    }

    /**
     * Create a new HybridClientJ with specified port.
     * 
     * @param port the port for Py4J communication
     */
    public HybridClientJ(int port) {
        try {
            // Start gateway server
            gateway = new GatewayServer(this, port);
            gateway.start();
            
            // Wait for Python connection
            long startTime = System.currentTimeMillis();
            while (!isConnected && (System.currentTimeMillis() - startTime) < CONNECTION_TIMEOUT_MS) {
                try {
                    pythonClient = gateway.getPythonServerEntryPoint(new Class[] {Object.class});
                    if (pythonClient != null) {
                        isConnected = true;
                        LOGGER.info("Successfully connected to Python HybridClient");
                    }
                } catch (Py4JException e) {
                    // Python not ready yet
                    try {
                        Thread.sleep(100);
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw new RuntimeException("Interrupted while waiting for Python connection", ie);
                    }
                }
            }
            
            if (!isConnected) {
                throw new RuntimeException("Failed to connect to Python HybridClient within timeout");
            }
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Failed to initialize HybridClientJ", e);
            throw new RuntimeException("Failed to initialize HybridClientJ", e);
        }
    }

    /**
     * Execute an action on a page.
     *
     * @param step natural language instruction
     * @param url  URL to navigate to (can be null)
     * @return a Map representing the JSON result with strict guarantees (no null/empty fields)
     * @throws RuntimeException if the action fails
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> act(String step, String url) {
        validateConnection();
        
        try {
            Object result = pythonClient.getClass()
                .getMethod("act", String.class, String.class)
                .invoke(pythonClient, step, url);
            
            if (result instanceof Map) {
                return sanitizeResult((Map<String, Object>) result);
            } else {
                throw new RuntimeException("Unexpected result type from act(): " + result.getClass());
            }
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Failed to execute action: " + step, e);
            
            // Return error result
            Map<String, Object> errorResult = new HashMap<>();
            errorResult.put("success", false);
            errorResult.put("action", step);
            errorResult.put("error", e.getMessage());
            errorResult.put("used_locator", "none");
            errorResult.put("duration_ms", 0);
            return errorResult;
        }
    }

    /**
     * Query for elements matching a phrase.
     *
     * @param phrase the search phrase
     * @param url URL to navigate to (can be null)
     * @return a Map representing the query result with strict JSON guarantees
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> query(String phrase, String url) {
        validateConnection();
        
        try {
            Object result = pythonClient.getClass()
                .getMethod("query", String.class, String.class)
                .invoke(pythonClient, phrase, url);
            
            if (result instanceof Map) {
                return sanitizeResult((Map<String, Object>) result);
            } else if (result instanceof List) {
                // If query returns a list, wrap it
                Map<String, Object> wrappedResult = new HashMap<>();
                wrappedResult.put("results", sanitizeList((List<?>) result));
                wrappedResult.put("count", ((List<?>) result).size());
                return wrappedResult;
            } else {
                throw new RuntimeException("Unexpected result type from query(): " + result.getClass());
            }
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Failed to query: " + phrase, e);
            
            // Return error result
            Map<String, Object> errorResult = new HashMap<>();
            errorResult.put("selector", "");
            errorResult.put("confidence", 0.0);
            errorResult.put("element", new HashMap<>());
            errorResult.put("rationale", "Query failed: " + e.getMessage());
            errorResult.put("error", e.getMessage());
            return errorResult;
        }
    }

    /**
     * Clear the embedding cache.
     * 
     * @return true if cache was cleared successfully
     */
    public boolean clearCache() {
        validateConnection();
        
        try {
            Object result = pythonClient.getClass()
                .getMethod("clear_cache")
                .invoke(pythonClient);
            return Boolean.TRUE.equals(result);
        } catch (Exception e) {
            LOGGER.log(Level.WARNING, "Failed to clear cache", e);
            return false;
        }
    }

    /**
     * Get cache statistics.
     * 
     * @return Map containing cache statistics
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> getCacheStats() {
        validateConnection();
        
        try {
            Object result = pythonClient.getClass()
                .getMethod("get_cache_stats")
                .invoke(pythonClient);
            
            if (result instanceof Map) {
                return sanitizeResult((Map<String, Object>) result);
            }
            return new HashMap<>();
        } catch (Exception e) {
            LOGGER.log(Level.WARNING, "Failed to get cache stats", e);
            return new HashMap<>();
        }
    }

    /**
     * Close the client and clean up resources.
     */
    public void close() {
        if (pythonClient != null) {
            try {
                pythonClient.getClass().getMethod("close").invoke(pythonClient);
            } catch (Exception e) {
                LOGGER.log(Level.WARNING, "Failed to close Python client", e);
            }
        }
    }

    /**
     * Shut down the gateway when done.
     */
    public void shutdown() {
        try {
            close();
        } finally {
            if (gateway != null) {
                gateway.shutdown();
            }
            isConnected = false;
            LOGGER.info("HybridClientJ shutdown complete");
        }
    }

    /**
     * Validate that we're connected to Python.
     * 
     * @throws IllegalStateException if not connected
     */
    private void validateConnection() {
        if (!isConnected || pythonClient == null) {
            throw new IllegalStateException("Not connected to Python HybridClient");
        }
    }

    /**
     * Sanitize a result Map to ensure no null or empty values (strict JSON).
     * 
     * @param map the map to sanitize
     * @return sanitized map
     */
    @SuppressWarnings("unchecked")
    private Map<String, Object> sanitizeResult(Map<String, Object> map) {
        Map<String, Object> sanitized = new HashMap<>();
        
        for (Map.Entry<String, Object> entry : map.entrySet()) {
            String key = entry.getKey();
            Object value = entry.getValue();
            
            if (value != null) {
                if (value instanceof String && !((String) value).isEmpty()) {
                    sanitized.put(key, value);
                } else if (value instanceof Map) {
                    Map<String, Object> sanitizedMap = sanitizeResult((Map<String, Object>) value);
                    if (!sanitizedMap.isEmpty()) {
                        sanitized.put(key, sanitizedMap);
                    }
                } else if (value instanceof List) {
                    List<?> sanitizedList = sanitizeList((List<?>) value);
                    if (!sanitizedList.isEmpty()) {
                        sanitized.put(key, sanitizedList);
                    }
                } else if (!(value instanceof String)) {
                    // Non-string values (numbers, booleans) are kept
                    sanitized.put(key, value);
                }
            }
        }
        
        return sanitized;
    }

    /**
     * Sanitize a list to ensure no null values.
     * 
     * @param list the list to sanitize
     * @return sanitized list
     */
    @SuppressWarnings("unchecked")
    private List<?> sanitizeList(List<?> list) {
        List<Object> sanitized = new ArrayList<>();
        
        for (Object item : list) {
            if (item != null) {
                if (item instanceof Map) {
                    sanitized.add(sanitizeResult((Map<String, Object>) item));
                } else if (item instanceof List) {
                    sanitized.add(sanitizeList((List<?>) item));
                } else if (!(item instanceof String) || !((String) item).isEmpty()) {
                    sanitized.add(item);
                }
            }
        }
        
        return sanitized;
    }

    /**
     * Main method for testing.
     */
    public static void main(String[] args) {
        HybridClientJ client = null;
        try {
            client = new HybridClientJ();
            
            // Test act
            Map<String, Object> actResult = client.act("Click login button", "https://example.com");
            System.out.println("Act result: " + actResult);
            
            // Test query
            Map<String, Object> queryResult = client.query("Find all buttons", "https://example.com");
            System.out.println("Query result: " + queryResult);
            
            // Test cache
            Map<String, Object> cacheStats = client.getCacheStats();
            System.out.println("Cache stats: " + cacheStats);
            
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            if (client != null) {
                client.shutdown();
            }
        }
    }
}