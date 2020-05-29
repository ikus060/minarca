/*
 * Copyright (C) 2020, IKUS Software inc. All rights reserved.
 * IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.model;

/**
 * Minarca Info
 * 
 * @author Patrik Dufresne
 * 
 */
public class MinarcaInfo {
    /**
     * Minarca server identity. Should be used to create known_hosts.
     */
    public String identity;
    /**
     * Minarca SSH remote host.
     */
    public String remotehost;
    /**
     * Minarca server version.
     */
    public String version;

}
