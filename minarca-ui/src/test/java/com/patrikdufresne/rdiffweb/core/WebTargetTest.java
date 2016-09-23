package com.patrikdufresne.rdiffweb.core;

import static net.jadler.Jadler.closeJadler;
import static net.jadler.Jadler.initJadler;
import static net.jadler.Jadler.onRequest;
import static net.jadler.Jadler.port;
import static net.jadler.Jadler.verifyThatRequest;
import static org.junit.Assert.assertEquals;

import java.io.IOException;
import java.nio.charset.Charset;
import java.util.Locale;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;

/**
 * Test the web target.
 * 
 * @author Patrik Dufresne
 * 
 */
public class WebTargetTest {

    @Before
    public void setUp() {
        initJadler();
    }

    @After
    public void tearDown() throws Exception {
        closeJadler();
    }

    /**
     * Test if getting page is working.
     * 
     * @throws IllegalStateException
     * @throws IOException
     */
    @Test
    public void testGet() throws IllegalStateException, IOException {
        // Mock response
        onRequest().havingMethodEqualTo("GET").havingPathEqualTo("/").respond().withStatus(200).withBody("TEST PAGE").withEncoding(Charset.forName("UTF-8"));

        // Get page.
        String location = new WebTarget("http://localhost:" + port()).target("/").getAsString();
        assertEquals(location, "TEST PAGE");
    }

    /**
     * Test if WebTarget send locale.
     * 
     * @throws IllegalStateException
     * @throws IOException
     */
    @Test
    public void testGetWithLocale() throws IllegalStateException, IOException {
        // Mock response
        onRequest().havingMethodEqualTo("GET").havingPathEqualTo("/").respond().withStatus(200).withBody("TEST PAGE").withEncoding(Charset.forName("UTF-8"));

        // Get page.
        String location = new WebTarget("http://localhost:" + port(), Locale.CANADA_FRENCH).target("/").getAsString();
        assertEquals(location, "TEST PAGE");

        // Verify Local
        verifyThatRequest().havingHeaderEqualTo("Accept-Language", "fr,fr-CA;q=0.5").receivedOnce();
    }
}
