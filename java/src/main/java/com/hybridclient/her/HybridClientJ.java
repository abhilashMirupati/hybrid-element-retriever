package com.hybridclient.her;

import py4j.GatewayServer;
import java.util.List;
import java.util.Map;

/**
 * Thin Java wrapper for the Python Hybrid Element Retriever.
 *
 * <p>This class uses Py4J to connect to a running Python process that
 * exposes an instance of {@code HybridClient}.  The Python side must
 * start a {@link py4j.GatewayServer} and register the client as the
 * entry point.  See the README in the Python project for setup
 * instructions.</p>
 */
public class HybridClientJ {
    private final GatewayServer gateway;
    private final Object pythonClient;

    /**
     * Start a new GatewayServer and obtain the Python HybridClient.
     */
    public HybridClientJ() {
        // Start a GatewayServer on an arbitrary port; Python will connect back
        gateway = new GatewayServer(null);
        gateway.start();
        // Obtain the entry point exported by Python; the Python code must
        // implement a method getHybridClient() that returns the HybridClient
        pythonClient = gateway.getPythonServerEntryPoint(new Class[] {Object.class});
    }

    /**
     * Execute an action on a page.
     *
     * @param step natural language instruction
     * @param url  optional URL
     * @return a Map representing the JSON result
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> act(String step, String url) {
        return (Map<String, Object>) gateway.getPythonServerEntryPoint(new Class[] {Object.class})
                .invoke("act", new Object[]{step, url});
    }

    /**
     * Query for locator candidates.
     *
     * @param phrase the search phrase
     * @param url optional URL
     * @return a List of locator candidate maps
     */
    @SuppressWarnings("unchecked")
    public List<Map<String, Object>> query(String phrase, String url) {
        return (List<Map<String, Object>>) gateway.getPythonServerEntryPoint(new Class[] {Object.class})
                .invoke("query", new Object[]{phrase, url});
    }

    /**
     * Convenience method to obtain ranked XPath strings for a phrase.
     */
    @SuppressWarnings("unchecked")
    public List<String> findXPaths(String phrase, String url) {
        return (List<String>) gateway.getPythonServerEntryPoint(new Class[] {Object.class})
                .invoke("findXPaths", new Object[]{phrase, url});
    }

    /**
     * Shut down the gateway when done.
     */
    public void shutdown() {
        gateway.shutdown();
    }
}