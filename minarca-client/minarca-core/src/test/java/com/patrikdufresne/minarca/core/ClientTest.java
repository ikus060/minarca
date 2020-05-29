/*
 * Copyright (C) 2020, IKUS Software inc. All rights reserved.
 * IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core;

import static net.jadler.Jadler.closeJadler;
import static net.jadler.Jadler.initJadler;
import static net.jadler.Jadler.onRequest;
import static net.jadler.Jadler.port;
import static org.junit.Assert.assertEquals;

import java.io.IOException;

import org.apache.http.client.HttpResponseException;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import com.patrikdufresne.minarca.core.model.CurrentUser;

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

    /**
     * Check if exception is raised when login page show error.
     * 
     * @throws IOException
     */
    @Test
    public void testLoginWithError() throws IOException {
        // Mock response
        onRequest().havingMethodEqualTo("GET").havingPathEqualTo("/api/currentuser/").respond().withStatus(401);

        // Test version
        Client client = new Client("http://localhost:" + port(), "user", "password");
        try {
            client.getCurrentUserInfo();
        } catch (HttpResponseException e) {
            assertEquals("Unauthorized", e.getMessage());
            assertEquals(401, e.getStatusCode());
        }

    }

    /**
     * Check result of get repositories when not repo.
     * 
     * @throws IOException
     */
    @Test
    public void testGetCurrentUserInfoEmpty() throws IOException {
        // Mock response
        onRequest()
                .havingMethodEqualTo("GET")
                .havingPathEqualTo("/api/currentuser/")
                .respond()
                .withStatus(200)
                .withBody(getClass().getResourceAsStream("currentuser_empty.json"));

        // Test
        Client client = new Client("http://localhost:" + port(), "user", "password");
        CurrentUser info = client.getCurrentUserInfo();
        assertEquals(0, info.repos.size());
    }

    /**
     * Check result of get repositories when not repo.
     * 
     * @throws IOException
     */
    @Test
    public void testGetCurrentUserInfo() throws IOException {
        // Mock response
        onRequest()
                .havingMethodEqualTo("GET")
                .havingPathEqualTo("/api/currentuser/")
                .respond()
                .withStatus(200)
                .withBody(getClass().getResourceAsStream("currentuser.json"));

        // Test
        Client client = new Client("http://localhost:" + port(), "user", "password");
        CurrentUser info = client.getCurrentUserInfo();
        assertEquals(3, info.repos.size());
    }

}
