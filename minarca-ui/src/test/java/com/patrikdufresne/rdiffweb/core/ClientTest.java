package com.patrikdufresne.rdiffweb.core;

import static net.jadler.Jadler.closeJadler;
import static net.jadler.Jadler.initJadler;
import static net.jadler.Jadler.onRequest;
import static net.jadler.Jadler.port;
import static org.junit.Assert.assertEquals;

import java.io.IOException;
import java.util.Collection;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;

/**
 * Test Client
 * 
 * @author Patrik Dufresne
 * 
 */
public class ClientTest {

    @Before
    public void setUp() {
        initJadler();
    }

    @After
    public void tearDown() throws Exception {
        closeJadler();
    }

    @Test
    public void testGetCurrentVersion() throws IOException {
        // Mock response
        onRequest().havingMethodEqualTo("GET").havingPathEqualTo("/").respond().withStatus(200).withBody(getClass().getResourceAsStream("login.html"));

        // Test version
        Client client = new Client("http://localhost:" + port(), "user", "password");
        String version = client.getCurrentVersion();
        assertEquals("0.9.1.dev1", version);
    }

    /**
     * Check if exception is raised when login page show error.
     * 
     * @throws IOException
     */
    @Test(expected = RdiffwebException.class)
    public void testLoginWithError() throws IOException {
        // Mock response
        onRequest().havingMethodEqualTo("GET").havingPathEqualTo("/").respond().withStatus(200).withBody(getClass().getResourceAsStream("login.html"));
        onRequest()
                .havingMethodEqualTo("POST")
                .havingPathEqualTo("/login/")
                .respond()
                .withStatus(200)
                .withBody(getClass().getResourceAsStream("login_invalid_credential.html"));

        // Test version
        Client client = new Client("http://localhost:" + port(), "user", "password");
        client.getRepositories();
    }

    /**
     * Check result of get repositories when not repo.
     * 
     * @throws IOException
     */
    @Test
    public void testGetRepositoriesEmpty() throws IOException {
        // Mock response
        onRequest()
                .havingMethodEqualTo("GET")
                .havingPathEqualTo("/")
                .respond()
                .withStatus(200)
                .withBody(getClass().getResourceAsStream("locations_empty.html"));

        // Test
        Client client = new Client("http://localhost:" + port(), "user", "password");
        Collection<Repository> repos = client.getRepositories();
        assertEquals(0, repos.size());
    }

    /**
     * Check result of get repositories when not repo.
     * 
     * @throws IOException
     */
    @Test
    public void testGetRepositories() throws IOException {
        // Mock response
        onRequest().havingMethodEqualTo("GET").havingPathEqualTo("/").respond().withStatus(200).withBody(getClass().getResourceAsStream("locations.html"));

        // Test
        Client client = new Client("http://localhost:" + port(), "user", "password");
        Collection<Repository> repos = client.getRepositories();
        assertEquals(2, repos.size());
    }

    /**
     * Check result of get repositories when not repo.
     * 
     * @throws IOException
     */
    @Test
    public void testGetRepository() throws IOException {
        // Mock response
        onRequest().havingMethodEqualTo("GET").havingPathEqualTo("/").respond().withStatus(200).withBody(getClass().getResourceAsStream("locations.html"));

        // Test
        Client client = new Client("http://localhost:" + port(), "user", "password");
        Repository repo = client.getRepositoryInfo("data");
        assertEquals("data", repo.getName());

    }

}
