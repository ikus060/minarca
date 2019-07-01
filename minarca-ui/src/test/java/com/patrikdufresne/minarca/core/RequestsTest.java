package com.patrikdufresne.minarca.core;

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

import com.patrikdufresne.minarca.core.RdiffwebException;
import com.patrikdufresne.minarca.core.Requests;

/**
 * Test the web target.
 * 
 * @author Patrik Dufresne
 * 
 */
public class RequestsTest {

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
        String location = new Requests("http://localhost:" + port()).target("/").text();
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
        String location = new Requests("http://localhost:" + port(), Locale.CANADA_FRENCH).target("/").text();
        assertEquals(location, "TEST PAGE");

        // Verify Local
        verifyThatRequest().havingHeaderEqualTo("Accept-Language", "fr,fr-CA;q=0.5").receivedOnce();
    }

    /**
     * Make sure alter info are not throwing exception.
     * 
     * @throws IOException
     * @throws IllegalStateException
     */
    @Test
    public void testGetWithAlertInfo() throws IllegalStateException, IOException {
        // Mock response
        onRequest()
                .havingMethodEqualTo("GET")
                .havingPathEqualTo("/")
                .respond()
                .withStatus(200)
                .withBody(
                        "<div class='alert alert-info alert-dismissible' role='alert'>"
                                + "<button type='button' class='close' data-dismiss='alert' aria-label='Close'><span aria-hidden='true'>×</span></button>"
                                + "You don't have any repositories configured."
                                + "</div>")
                .withEncoding(Charset.forName("UTF-8"));

        // Get page.
        new Requests("http://localhost:" + port(), Locale.CANADA_FRENCH).target("/").text();
    }

    /**
     * Make sure alter info are not throwing exception.
     * 
     * @throws IOException
     * @throws IllegalStateException
     */
    @Test(expected = RdiffwebException.class)
    public void testGetWithAlertDanger() throws IllegalStateException, IOException {
        // Mock response
        onRequest()
                .havingMethodEqualTo("GET")
                .havingPathEqualTo("/")
                .respond()
                .withStatus(200)
                .withBody(
                        "<div class='alert alert-danger alert-dismissible' role='alert'>"
                                + "<button type='button' class='close' data-dismiss='alert' aria-label='Close'><span aria-hidden='true'>×</span></button>"
                                + "This is an exception."
                                + "</div>")
                .withEncoding(Charset.forName("UTF-8"));

        // Get page.
        new Requests("http://localhost:" + port(), Locale.CANADA_FRENCH).target("/").text();
    }
}
