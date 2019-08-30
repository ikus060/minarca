/*
 * Copyright (C) 2019, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core;

public class ServerException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    public ServerException(String message) {
        super(message);
    }

}
