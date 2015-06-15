/*
 * Copyright (C) 2015, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core;

/**
 * 
 * @author Patrik Dufresne
 * 
 */
public class Client extends com.patrikdufresne.rdiffweb.core.Client {

    /**
     * Create a new instance of client.
     * 
     * @param username
     *            the username
     * @param password
     *            the password
     */
    public Client(String username, String password) {
        super(API.BASE_URL, username, password);
    }

}
