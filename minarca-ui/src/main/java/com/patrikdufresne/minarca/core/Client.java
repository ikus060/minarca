/*
 * Copyright (c) 2014, Patrik Dufresne Service Logiciel. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core;

import java.net.MalformedURLException;

import org.jsoup.helper.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.internal.InternalHttpClient;

/**
 * Used to represent a connection to minarca. Either via HTTP or SSH or both.
 * 
 * @author Patrik Dufresne
 * 
 */
public class Client {
    /**
     * The logger.
     */
    private static final transient Logger LOGGER = LoggerFactory.getLogger(Client.class);
    /**
     * Locations page.
     */
    private static final String PAGE_LOCATIONS = "/";
    /**
     * Reference to the internal HTTP client used to request pages.
     */
    private InternalHttpClient http;

    private String password;

    private String username;

    /**
     * Create a new minarca client.
     * 
     * @param username
     *            the username.
     * @param password
     *            the password.
     * @throws APIException
     * @throws MalformedURLException
     */
    protected Client(String username, String password) throws APIException {
        this(API.BASE_URL, username, password);
    }

    /**
     * Private constructor providing default URL.
     * 
     * @param url
     * @param username
     * @param password
     * @throws APIException
     */
    private Client(String url, String username, String password) throws APIException {
        Validate.notNull(this.username = username);
        Validate.notNull(this.password = password);
        // Check credentials by requesting the locations page.
        LOGGER.debug("authentication to minarca as {}", username);
        this.http = new InternalHttpClient(API.BASE_URL, username, password);
        this.http.get(PAGE_LOCATIONS);
    }

    /**
     * Register a new computer.
     * <p>
     * A successful link of this computer will generate a new configuration file.
     * <p>
     * This implementation will generate public and private keys for putty. The public key will be sent to minarca. The
     * computer name is added to the comments.
     * 
     * 
     * @param computername
     *            friendly name to represent this computer.
     * @throws APIException
     *             if the keys can't be created.
     * @throws IllegalAccessException
     *             if the computer name is not valid.
     */
    public void link(String computername) throws APIException {
        API.instance().link(this.username, this.password, computername);
    }

}
