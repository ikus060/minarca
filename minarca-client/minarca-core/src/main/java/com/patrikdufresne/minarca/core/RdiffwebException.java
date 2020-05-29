/*
 * Copyright (C) 2020, IKUS Software inc. All rights reserved.
 * IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core;

import java.io.IOException;

import org.apache.http.HttpResponse;

public class RdiffwebException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    private HttpResponse response;

    public RdiffwebException(String message) {
        this(message, null);
    }

    public RdiffwebException(String message, HttpResponse response) {
        super(message);
        this.response = response;
    }

    public HttpResponse getResponse() {
        return this.response;
    }

    public String getResponseToString() throws IllegalStateException, IOException {
        if (this.response == null) {
            return null;
        }
        return Requests.toString(this.response);
    }

}
