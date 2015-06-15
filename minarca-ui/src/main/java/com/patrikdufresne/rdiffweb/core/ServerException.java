/*
 * Copyright (c) 2014, Patrik Dufresne Service Logiciel. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.rdiffweb.core;

public class ServerException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    public ServerException(String message) {
        super(message);
    }

}
