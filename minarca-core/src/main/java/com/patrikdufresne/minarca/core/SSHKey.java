/*
 * Copyright (C) 2020, IKUS Software inc. All rights reserved.
 * IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core;

/**
 * Represent an SSH key
 * 
 * @author Patrik Dufresne
 * 
 */
public class SSHKey {

    private String fingerprint;

    private String id;

    private String title;

    public String getFingerprint() {
        return fingerprint;
    }

    public String getId() {
        return id;
    }

    public String getTitle() {
        return title;
    }

    public void setFingerprint(String fingerprint) {
        this.fingerprint = fingerprint;
    }

    public void setId(String id) {
        this.id = id;
    }

    public void setTitle(String title) {
        this.title = title;
    }

}
