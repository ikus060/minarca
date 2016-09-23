package com.patrikdufresne.rdiffweb.core;

import static net.jadler.Jadler.closeJadler;
import static net.jadler.Jadler.initJadler;
import static net.jadler.Jadler.onRequest;
import static net.jadler.Jadler.port;
import static org.junit.Assert.assertEquals;

import java.io.IOException;
import java.nio.charset.Charset;

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
        onRequest()
                .havingMethodEqualTo("GET")
                .havingPathEqualTo("/login")
                .respond()
                .withStatus(200)
                .withBody("..<meta name=\"app-version\" content=\"1.1.1\">..")
                .withEncoding(Charset.forName("UTF-8"));

        // Test version
        Client client = new Client("http://localhost:" + port(), "user", "password");
        String version = client.getCurrentVersion();
        assertEquals("1.1.1", version);
    }

    /**
     * Check if exception is raised when login page show error.
     * 
     * @throws IOException
     */
    @Test(expected = RdiffwebException.class)
    public void testLoginWithError() throws IOException {
        // Mock response
        onRequest()
                .havingMethodEqualTo("GET")
                .havingPathEqualTo("/")
                .respond()
                .withStatus(200)
                .withBody("<form class='form-signin' role='form' method='post' action='/login/' id=\"form-login\">");
        onRequest()
                .havingMethodEqualTo("POST")
                .havingPathEqualTo("/login/")
                .respond()
                .withStatus(200)
                .withBody(
                        "<div class='alert alert-warning alert-dismissible' role='alert'>"
                                + "<button type='button' class='close' data-dismiss='alert' aria-label='Close'><span aria-hidden='true'>×</span></button>"
                                + "<strong>Warning!</strong> Invalid username or password."
                                + "</div>")
                .withEncoding(Charset.forName("UTF-8"));

        // Test version
        Client client = new Client("http://localhost:" + port(), "user", "password");
        client.getRepositories();
    }

}
