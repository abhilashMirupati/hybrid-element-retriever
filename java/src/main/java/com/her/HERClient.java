package com.her;

import py4j.GatewayServer;
import py4j.Py4JException;
import py4j.Gateway;
import py4j.GatewayServerListener;
import py4j.Py4JServerConnection;

import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.ArrayList;
import java.util.concurrent.TimeUnit;
import java.io.IOException;
import java.io.BufferedReader;
import java.io.InputStreamReader;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * Java client for Hybrid Element Retriever (HER).
 * Provides a thin wrapper around the Python HER library using Py4J.
 */
public class HERClient implements AutoCloseable {
    private static final Logger logger = LoggerFactory.getLogger(HERClient.class);
    private static final int DEFAULT_PORT = 25333;
    private static final int CONNECTION_TIMEOUT_MS = 30000;
    
    private Process pythonProcess;
    private Gateway gateway;
    private Object herClient;
    private ObjectMapper objectMapper;
    private boolean isConnected;
    
    /**
     * Create a new HER client with default settings.
     */
    public HERClient() throws IOException {
        this(DEFAULT_PORT, true);
    }
    
    /**
     * Create a new HER client.
     * 
     * @param port Port for Py4J gateway
     * @param autoStart Whether to auto-start Python gateway server
     */
    public HERClient(int port, boolean autoStart) throws IOException {
        this.objectMapper = new ObjectMapper();
        this.isConnected = false;
        
        if (autoStart) {
            startPythonGateway(port);
            connectToGateway(port);
        }
    }
    
    /**
     * Start the Python gateway server.
     */
    private void startPythonGateway(int port) throws IOException {
        logger.info("Starting Python HER gateway on port {}", port);
        
        ProcessBuilder pb = new ProcessBuilder(
            "python", "-m", "her.gateway_server", 
            "--port", String.valueOf(port)
        );
        
        pb.redirectErrorStream(true);
        pythonProcess = pb.start();
        
        // Start thread to read Python output
        new Thread(() -> {
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(pythonProcess.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    logger.debug("Python: {}", line);
                }
            } catch (IOException e) {
                logger.error("Error reading Python output", e);
            }
        }).start();
        
        // Wait for Python to start
        try {
            Thread.sleep(2000);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
    
    /**
     * Connect to the Python gateway.
     */
    private void connectToGateway(int port) {
        logger.info("Connecting to Python gateway on port {}", port);
        
        long startTime = System.currentTimeMillis();
        Exception lastException = null;
        
        while (System.currentTimeMillis() - startTime < CONNECTION_TIMEOUT_MS) {
            try {
                gateway = new Gateway(new java.net.InetSocketAddress("localhost", port));
                herClient = gateway.entry_point;
                isConnected = true;
                logger.info("Successfully connected to Python HER gateway");
                return;
            } catch (Exception e) {
                lastException = e;
                try {
                    Thread.sleep(500);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }
        
        throw new RuntimeException("Failed to connect to Python gateway", lastException);
    }
    
    /**
     * Query for elements matching a natural language phrase.
     * 
     * @param phrase Natural language description
     * @return Query results
     */
    public QueryResult query(String phrase) {
        return query(phrase, null);
    }
    
    /**
     * Query for elements matching a natural language phrase.
     * 
     * @param phrase Natural language description
     * @param url Optional URL to navigate to first
     * @return Query results
     */
    public QueryResult query(String phrase, String url) {
        ensureConnected();
        
        try {
            Object result = gateway.invoke(herClient, "query", phrase, url);
            return parseQueryResult(result);
        } catch (Py4JException e) {
            logger.error("Query failed: {}", e.getMessage());
            return new QueryResult(false, e.getMessage());
        }
    }
    
    /**
     * Find XPath selectors for a phrase.
     * 
     * @param phrase Natural language description
     * @return List of XPath selectors
     */
    public List<String> findXPaths(String phrase) {
        return findXPaths(phrase, null);
    }
    
    /**
     * Find XPath selectors for a phrase.
     * 
     * @param phrase Natural language description
     * @param url Optional URL to navigate to first
     * @return List of XPath selectors
     */
    @SuppressWarnings("unchecked")
    public List<String> findXPaths(String phrase, String url) {
        ensureConnected();
        
        try {
            Object result = gateway.invoke(herClient, "findXPaths", phrase, url);
            if (result instanceof List) {
                return (List<String>) result;
            }
            return new ArrayList<>();
        } catch (Py4JException e) {
            logger.error("FindXPaths failed: {}", e.getMessage());
            return new ArrayList<>();
        }
    }
    
    /**
     * Click on an element.
     * 
     * @param phrase Natural language description
     * @return Action result
     */
    public ActionResult click(String phrase) {
        ensureConnected();
        
        try {
            Object result = gateway.invoke(herClient, "click", phrase);
            return parseActionResult(result);
        } catch (Py4JException e) {
            logger.error("Click failed: {}", e.getMessage());
            return new ActionResult(false, e.getMessage());
        }
    }
    
    /**
     * Type text into an element.
     * 
     * @param phrase Natural language description
     * @param text Text to type
     * @return Action result
     */
    public ActionResult typeText(String phrase, String text) {
        ensureConnected();
        
        try {
            Object result = gateway.invoke(herClient, "type_text", phrase, text);
            return parseActionResult(result);
        } catch (Py4JException e) {
            logger.error("Type text failed: {}", e.getMessage());
            return new ActionResult(false, e.getMessage());
        }
    }
    
    /**
     * Navigate to a URL.
     * 
     * @param url URL to navigate to
     * @return Success status
     */
    public boolean navigate(String url) {
        ensureConnected();
        
        try {
            gateway.invoke(herClient, "navigate", url);
            return true;
        } catch (Py4JException e) {
            logger.error("Navigation failed: {}", e.getMessage());
            return false;
        }
    }
    
    /**
     * Take a screenshot.
     * 
     * @param filepath Path to save screenshot
     * @return Success status
     */
    public boolean screenshot(String filepath) {
        ensureConnected();
        
        try {
            gateway.invoke(herClient, "screenshot", filepath);
            return true;
        } catch (Py4JException e) {
            logger.error("Screenshot failed: {}", e.getMessage());
            return false;
        }
    }
    
    /**
     * Ensure gateway is connected.
     */
    private void ensureConnected() {
        if (!isConnected) {
            throw new IllegalStateException("Not connected to Python gateway");
        }
    }
    
    /**
     * Parse query result from Python.
     */
    @SuppressWarnings("unchecked")
    private QueryResult parseQueryResult(Object result) {
        if (result instanceof Map) {
            Map<String, Object> map = (Map<String, Object>) result;
            
            if (map.containsKey("ok") && !(Boolean) map.get("ok")) {
                return new QueryResult(false, (String) map.get("error"));
            }
            
            if (map.containsKey("selector")) {
                return new QueryResult(
                    (String) map.get("selector"),
                    ((Number) map.getOrDefault("confidence", 0.0)).doubleValue(),
                    (Map<String, Object>) map.get("element")
                );
            }
        } else if (result instanceof List) {
            List<Map<String, Object>> list = (List<Map<String, Object>>) result;
            return new QueryResult(list);
        }
        
        return new QueryResult(false, "Unknown result format");
    }
    
    /**
     * Parse action result from Python.
     */
    @SuppressWarnings("unchecked")
    private ActionResult parseActionResult(Object result) {
        if (result instanceof Map) {
            Map<String, Object> map = (Map<String, Object>) result;
            boolean ok = (Boolean) map.getOrDefault("ok", false);
            String message = (String) map.get("message");
            String error = (String) map.get("error");
            
            return new ActionResult(ok, ok ? message : error);
        }
        
        return new ActionResult(false, "Unknown result format");
    }
    
    /**
     * Close the client and cleanup resources.
     */
    @Override
    public void close() {
        if (gateway != null) {
            try {
                gateway.shutdown();
            } catch (Exception e) {
                logger.error("Error shutting down gateway", e);
            }
        }
        
        if (pythonProcess != null) {
            try {
                pythonProcess.destroyForcibly();
                pythonProcess.waitFor(5, TimeUnit.SECONDS);
            } catch (Exception e) {
                logger.error("Error stopping Python process", e);
            }
        }
        
        isConnected = false;
    }
    
    /**
     * Query result class.
     */
    public static class QueryResult {
        private final boolean success;
        private final String error;
        private final String selector;
        private final double confidence;
        private final Map<String, Object> element;
        private final List<Map<String, Object>> elements;
        
        public QueryResult(boolean success, String error) {
            this.success = success;
            this.error = error;
            this.selector = null;
            this.confidence = 0.0;
            this.element = null;
            this.elements = null;
        }
        
        public QueryResult(String selector, double confidence, Map<String, Object> element) {
            this.success = true;
            this.error = null;
            this.selector = selector;
            this.confidence = confidence;
            this.element = element;
            this.elements = null;
        }
        
        public QueryResult(List<Map<String, Object>> elements) {
            this.success = true;
            this.error = null;
            this.selector = null;
            this.confidence = 0.0;
            this.element = null;
            this.elements = elements;
        }
        
        // Getters
        public boolean isSuccess() { return success; }
        public String getError() { return error; }
        public String getSelector() { return selector; }
        public double getConfidence() { return confidence; }
        public Map<String, Object> getElement() { return element; }
        public List<Map<String, Object>> getElements() { return elements; }
    }
    
    /**
     * Action result class.
     */
    public static class ActionResult {
        private final boolean success;
        private final String message;
        
        public ActionResult(boolean success, String message) {
            this.success = success;
            this.message = message;
        }
        
        public boolean isSuccess() { return success; }
        public String getMessage() { return message; }
    }
    
    /**
     * Main method for testing.
     */
    public static void main(String[] args) {
        try (HERClient client = new HERClient()) {
            // Test query
            QueryResult result = client.query("Find submit button");
            System.out.println("Query success: " + result.isSuccess());
            
            if (result.isSuccess() && result.getSelector() != null) {
                System.out.println("Selector: " + result.getSelector());
                System.out.println("Confidence: " + result.getConfidence());
            }
            
            // Test XPath finding
            List<String> xpaths = client.findXPaths("Find email input");
            System.out.println("Found " + xpaths.size() + " XPaths");
            
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}